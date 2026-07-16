import os
import shutil
import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from semantic_finance_etl.etl.orchestration.pipeline_executor import PipelineExecutor


@pytest.fixture
def e2e_config_dir():
    """Create an isolated configuration directory and database for E2E testing."""
    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        configs_src = Path("tests/samples/configs")
        
        # Copy configs to temp dir
        shutil.copytree(configs_src, temp_path / "configs")
        
        # Create a temp output db and temp source db
        output_db_path = temp_path / "output.db"
        source_db_path = temp_path / "source.db"
        
        shutil.copy2(Path("tests/samples/dbs/companies.db"), source_db_path)
        
        # Update runtime.yaml to point to output.db and set log_dir
        runtime_yaml = temp_path / "configs" / "runtime.yaml"
        runtime_content = runtime_yaml.read_text()
        runtime_content = runtime_content.replace(
            "tests/output/app4.db", str(output_db_path).replace("\\", "/")
        )
        # Append log_dir
        log_dir_path = temp_path / "logs"
        runtime_content += f"\nlog_dir: '{log_dir_path.as_posix()}'\n"
        
        # Update hook search path to absolute so the temp runner can find it
        abs_hook_path = configs_src.absolute() / "hooks"
        runtime_content = runtime_content.replace(
            "tests/samples/configs/hooks", str(abs_hook_path).replace("\\", "/")
        )
        runtime_yaml.write_text(runtime_content)
        
        # Update sources to point to our temp source.db
        source_yaml = temp_path / "configs" / "sources" / "investment_backups.yaml"
        source_content = source_yaml.read_text()
        # Find path: ... and replace it with temp_path
        new_source_content = []
        for line in source_content.splitlines():
            if line.startswith("path:"):
                new_source_content.append(f"path: {temp_path.as_posix()}")
            elif line.startswith("include_patterns:"):
                new_source_content.append("include_patterns: ['source.db']")
            else:
                new_source_content.append(line)
        source_yaml.write_text("\n".join(new_source_content))
        
        yield {
            "config_dir": temp_path / "configs",
            "output_db": output_db_path,
            "source_db": source_db_path,
        }
        
        # Clean up logger so Windows doesn't hold the file lock during teardown
        import logging
        root_logger = logging.getLogger("semantic_finance_etl")
        for handler in root_logger.handlers[:]:
            handler.close()
            root_logger.removeHandler(handler)


def test_full_pipeline_idempotency_and_modifications(e2e_config_dir):
    config_dir = e2e_config_dir["config_dir"]
    output_db = e2e_config_dir["output_db"]
    source_db = e2e_config_dir["source_db"]
    
    # ---------------------------------------------------------
    # RUN 1: Initial load
    # ---------------------------------------------------------
    summary_1 = PipelineExecutor().run(config_dir)
    assert summary_1.error is None
    
    conn = sqlite3.connect(output_db)
    conn.row_factory = sqlite3.Row
    import sqlite_vec
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as c FROM companies")
        initial_count = cur.fetchone()["c"]
        assert initial_count == 55991
        
        cur.execute("SELECT COUNT(*) as c FROM etl_semantic_index WHERE source_table = 'companies'")
        assert cur.fetchone()["c"] == 55991
        
        cur.execute("SELECT COUNT(*) as c FROM etl_semantic_index WHERE source_table = 'industry_stats'")
        assert cur.fetchone()["c"] == 149
    finally:
        conn.close()
    
    # ---------------------------------------------------------
    # RUN 2: Idempotency (run again with no changes)
    # ---------------------------------------------------------
    summary_2 = PipelineExecutor().run(config_dir)
    assert summary_2.error is None
    
    conn = sqlite3.connect(output_db)
    conn.row_factory = sqlite3.Row
    import sqlite_vec
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as c FROM companies")
        idempotent_count = cur.fetchone()["c"]
        assert idempotent_count == 55991  # Row count should NOT increase
        
        cur.execute("SELECT COUNT(*) as c FROM etl_semantic_index WHERE source_table = 'companies'")
        assert cur.fetchone()["c"] == 55991
        
        cur.execute("SELECT COUNT(*) as c FROM etl_semantic_index WHERE source_table = 'industry_stats'")
        assert cur.fetchone()["c"] == 149
    finally:
        conn.close()
    
    # ---------------------------------------------------------
    # DATA MODIFICATION: Update existing row & insert new row
    # ---------------------------------------------------------
    source_conn = sqlite3.connect(source_db)
    try:
        scur = source_conn.cursor()
        
        # 1. Update existing company
        # We change 'current_employees' for ID 159 (global computer services llc)
        scur.execute(
            "UPDATE companies SET current_employees = ? WHERE id = ?",
            ("9999", "159")
        )
        
        # 2. Insert new company
        scur.execute(
            "INSERT INTO companies (id, name, domain, year_founded, industry, locality, country, current_employees, total_employees) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("999999", "Test Corp E2E", "teste2e.com", "2026.0", "AI Testing", "Test City", "Testland", "42", "42")
        )
        source_conn.commit()
    finally:
        source_conn.close()
    
    # ---------------------------------------------------------
    # RUN 3: Incremental load
    summary_3 = PipelineExecutor().run(config_dir)
    assert summary_3.error is None
    for sr in summary_3.semantic_results:
        assert sr.error is None
        assert sr.indexing_result.error is None
    
    conn = sqlite3.connect(output_db)
    conn.row_factory = sqlite3.Row
    import sqlite_vec
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    try:
        cur = conn.cursor()
        
        # The new row should be added
        cur.execute("SELECT COUNT(*) as c FROM companies")
        final_count = cur.fetchone()["c"]
        assert final_count == 55992
        
        # The updated row should reflect the new data due to upsert load_mode
        cur.execute("SELECT current_employees FROM companies WHERE id = '159'")
        updated_emp = cur.fetchone()["current_employees"]
        assert updated_emp == 9999
        
        # The derived stats table should reflect the new company
        cur.execute("SELECT company_count FROM industry_stats WHERE industry = 'AI TESTING'")
        ai_testing_count = cur.fetchone()["company_count"]
        assert ai_testing_count == 1
        
        # New derived-on-derived table check
        cur.execute("SELECT COUNT(*) as c FROM country_industry_summary")
        country_industry_count = cur.fetchone()["c"]
        assert country_industry_count > 100  # ensures it was populated
        
        # Verify the percentage was calculated (should be 1.0 for the newly inserted row since it's the only one)
        cur.execute("SELECT percent_of_global FROM country_industry_summary WHERE industry = 'AI TESTING'")
        ai_testing_pct = cur.fetchone()["percent_of_global"]
        assert ai_testing_pct == 1.0
        
        # ---------------------------------------------------------
        # SCHEMA & METADATA ASSERTIONS (Enterprise Grade Checks)
        # ---------------------------------------------------------
        
        # 1. Assert _record_hash exists and is populated in Canonical Tables
        cur.execute("SELECT _record_hash, _file_hash FROM companies LIMIT 5")
        for row in cur.fetchall():
            assert row["_record_hash"] is not None
            assert row["_file_hash"] is not None
            
        # 2. Assert _record_hash exists and is populated in Derived Tables
        cur.execute("SELECT _record_hash FROM industry_stats LIMIT 5")
        for row in cur.fetchall():
            assert row["_record_hash"] is not None
            
        # 3. Assert Primary Key constraints are configured correctly
        cur.execute("PRAGMA table_info(companies)")
        companies_cols = {row["name"]: row for row in cur.fetchall()}
        assert companies_cols["id"]["pk"] > 0
        
        # 4. Assert Foreign Key constraints are configured correctly
        cur.execute("PRAGMA foreign_key_list(country_industry_summary)")
        fks = cur.fetchall()
        assert len(fks) > 0
        assert fks[0]["table"] == "industry_stats"
        assert fks[0]["from"] == "industry"
        assert fks[0]["to"] == "industry"
        
        # 5. Assert Indexes are configured correctly
        cur.execute("PRAGMA index_list(companies)")
        indexes = {row["name"]: row for row in cur.fetchall()}
        assert any("industry" in idx for idx in indexes)  # Assuming industry is indexed
        
        # Semantic index should have increased by 1 (the 1 new document; the updated document replaces its old chunk cleanly)
        cur.execute("SELECT COUNT(*) as c FROM etl_semantic_index WHERE source_table = 'companies'")
        assert cur.fetchone()["c"] == 55992
        
        # We inserted 1 new company with "AI Testing" industry, so industry count increases by 1
        cur.execute("SELECT COUNT(*) as c FROM etl_semantic_index WHERE source_table = 'industry_stats'")
        assert cur.fetchone()["c"] == 150
        
        # Verify vector tables are also present
        cur.execute("SELECT COUNT(*) as c FROM etl_semantic_vectors")
        assert cur.fetchone()["c"] == 55992 + 150
        
        # Verify logs were created
        log_file = config_dir.parent / "logs" / "etl.log"
        assert log_file.exists()
        log_content = log_file.read_text()
        assert "Starting pipeline execution" in log_content

    finally:
        conn.close()
