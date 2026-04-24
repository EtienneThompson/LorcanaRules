from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class CardImages(BaseModel):
    model_config = ConfigDict(extra="ignore")
    full: str
    thumbnail: str
    foilMask: str | None = None
    varnishMask: str | None = None


class FormatAllowance(BaseModel):
    model_config = ConfigDict(extra="ignore")
    allowed: bool
    allowedUntilDate: str | None = None
    rotationGroup: int | None = None


class CardVariant(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: int
    code: str
    number: int
    rarity: str
    setCode: str
    setName: str
    foilTypes: list[str]
    images: CardImages
    flavorText: str | None = None
    artists: list[str]
    baseId: int | None = None
    promoGrouping: str | None = None
    promoSource: str | None = None
    promoSourceCategory: str | None = None
    varnishType: str | None = None


class CardResult(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    score: float = Field(alias="@search.score", default=0.0)
    id: int
    name: str
    fullName: str
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
    keywordAbilities: list[str] | None = None
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
    # Additional printings (promos, specialty reprints)
    variants: list[CardVariant] | None = None
