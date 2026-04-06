from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class RuleResult(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    score: float = Field(alias="@search.score", default=0.0)
    rule_id: str
    sections: list[str]
    rule_text: str = Field(alias="chunk")
    date: date
