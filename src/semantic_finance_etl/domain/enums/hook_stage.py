from enum import StrEnum


class HookStage(StrEnum):
    POST_READ = "post_read"
    PRE_APPEND = "pre_append"
    POST_APPEND = "post_append"
    PRE_VALIDATE = "pre_validate"
    POST_VALIDATE = "post_validate"
    PRE_LOAD = "pre_load"
    POST_LOAD = "post_load"
    PRE_DERIVE = "pre_derive"
    POST_DERIVE = "post_derive"
    PRE_SEMANTIC = "pre_semantic"
    POST_SEMANTIC = "post_semantic"
