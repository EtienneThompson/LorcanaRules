from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class CardAbility(BaseModel):
    model_config = ConfigDict(extra="ignore")
    type: str
    fullText: str
    # keyword ability fields
    keyword: str | None = None
    keywordValue: str | None = None
    keywordValueNumber: float | None = None
    reminderText: str | None = None
    # activated ability fields
    costs: list[str] | None = None
    costsText: str | None = None
    # named ability fields (triggered/activated/static)
    name: str | None = None
    effect: str | None = None


class CardImages(BaseModel):
    model_config = ConfigDict(extra="ignore")
    full: str
    thumbnail: str
    foilMask: str | None = None


class FormatAllowance(BaseModel):
    model_config = ConfigDict(extra="ignore")
    allowed: bool
    allowedUntilDate: str | None = None
    rotationGroup: int | None = None


class ReprintReference(BaseModel):
    id: int
    setCode: str


class CardResult(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    score: float = Field(alias="@search.score", default=0.0)
    id: int
    name: str
    version: str | None = None
    fullName: str
    simpleName: str
    type: str
    color: str
    cost: int
    inkwell: bool
    rarity: str
    setCode: str
    setName: str
    number: int
    code: str
    story: str | None = None
    subtypes: list[str]
    artists: list[str]
    artistsNormalized: list[str] | None = None
    keywordAbilities: list[str] | None = None
    abilities: list[CardAbility]
    fullText: str | None = None
    fullTextSections: list[str]
    flavorText: str | None = None
    foilTypes: list[str]
    images: CardImages
    allowedInFormats: dict[str, FormatAllowance]
    allowedInTournamentsFromDate: str | None = None
    completeCardText: str = Field(alias="chunk")
    date: date
    # Character/Location stats
    strength: int | None = None
    willpower: int | None = None
    lore: int | None = None
    # Location-only
    moveCost: int | None = None
    # Enchanted variant reference
    enchantedId: int | None = None
    # Reprint references
    reprintedAsIds: list[ReprintReference] | None = None
