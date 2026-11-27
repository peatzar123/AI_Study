from pydantic import BaseModel, Field, model_validator

THEME_BY_PREFIX = {
    "5": "Organizational",
    "6": "People",
    "7": "Physical",
    "8": "Technological",
}


class ISO27001Control(BaseModel):
    id: str
    theme: str
    name: str
    description: str

    @model_validator(mode="after")
    def check_theme_and_text(self):
        prefix = self.id.split(".")[0]
        expected_theme = THEME_BY_PREFIX.get(prefix)
        if expected_theme != self.theme:
            raise ValueError(f"Control {self.id} has invalid theme '{self.theme}' (expected '{expected_theme}')")
        if not self.name.strip() or not self.description.strip():
            raise ValueError(f"Control {self.id} must have non-empty name and description")
        return self


class StandardItem(BaseModel):
    id: str
    name: str
    description: str


class ControlMapping(BaseModel):
    from_ref: str = Field(alias="from")
    to_ref: str = Field(alias="to")
    reason: str


class ControlCatalog(BaseModel):
    versions: dict[str, str]
    iso27001: list[ISO27001Control]
    iso42001: list[StandardItem]
    pdpa: list[StandardItem]
    mappings: list[ControlMapping]

    @model_validator(mode="after")
    def check_catalog_completeness(self):
        ids = [c.id for c in self.iso27001]
        if len(ids) != 93 or len(set(ids)) != 93:
            raise ValueError(f"ISO 27001 must have exactly 93 unique controls (got {len(ids)})")
        if len(self.iso42001) == 0:
            raise ValueError("ISO 42001 controls cannot be empty")
        if len(self.mappings) < 10:
            raise ValueError(f"Must have at least 10 cross-mappings (got {len(self.mappings)})")
        return self