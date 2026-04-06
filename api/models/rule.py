from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class RuleResult(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    rule_id: str
    sections: list[str]
    rule_text: str = Field(alias="chunk")
    date: date
