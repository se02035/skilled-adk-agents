from pydantic import BaseModel, Field


class SkillElement(BaseModel):
    """
    Represents a discovered agent skill and its metadata.
    Review the description and name to decide if you want to use this skill.
    """

    uri: str = Field(
        description="The unique URI for the skill. Pass this exact URI to the read_skill tool to get its instructions."
    )
    description: str = Field(
        description="A brief explanation of what the skill does and when it should be used."
    )
    name: str = Field(description="The unique name identifying the skill.")
    root_directory: str = Field(
        description="The absolute path to the skill's root directory on the local file system."
    )
