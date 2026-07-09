"""
The extraction schema. This Pydantic model IS the contract with the LLM:
OpenAI's structured-output mode forces the model to return exactly these fields.
Edit the fields/descriptions here and the whole app updates automatically.
"""
from typing import Optional, Literal
from pydantic import BaseModel, Field


class HomeVisitExtraction(BaseModel):
    # --- Basics ---
    age: Optional[int] = Field(
        None, description="Participant's age in years. Null if not stated."
    )
    living_situation: str = Field(
        description="Who the participant lives with and housing type "
        "(e.g., 'lives alone in a two-story house', 'with spouse', 'assisted living')."
    )

    # --- Health ---
    health_concerns: list[str] = Field(
        default_factory=list,
        description="Diagnosed conditions or diseases the participant has "
        "(e.g., diabetes, hypertension, arthritis, heart failure, dementia, "
        "depression, vision or hearing loss). Include the condition even when "
        "it is mentioned alongside medications. Empty list if none.",
    )
    medication_issues: list[str] = Field(
        default_factory=list,
        description="Problems MANAGING medications only — missed doses, "
        "confusion about doses, doubling up, unmanaged regimens. Do NOT list "
        "the medical conditions themselves here. Empty list if none.",
    )
    cognitive_concerns: list[str] = Field(
        default_factory=list,
        description="Memory, orientation, or cognitive issues observed. "
        "Empty list if none.",
    )
    mental_health_indicators: list[str] = Field(
        default_factory=list,
        description="Mood, grief, anxiety, depression, or emotional-wellbeing "
        "signals. Empty list if none.",
    )

    # --- Functional / daily living ---
    adl_independence: Literal[
        "independent", "needs some help", "dependent", "unclear"
    ] = Field(
        description="Ability to perform activities of daily living (bathing, "
        "dressing, eating, mobility). 'unclear' if not described."
    )
    mobility_aids: list[str] = Field(
        default_factory=list,
        description="Assistive devices used (cane, walker, wheelchair, rollator). "
        "Empty list if none.",
    )

    # --- Fall risk ---
    fall_risk: Literal["none", "low", "moderate", "high", "unknown"] = Field(
        description="Overall fall-risk level implied by the note."
    )
    fall_history: str = Field(
        description="Summary of any past falls, or 'none reported'."
    )

    # --- Home safety ---
    safety_concerns: list[str] = Field(
        default_factory=list,
        description="Home/environmental safety hazards (rugs, stairs, stove, "
        "no smoke detector, etc.). Empty list if none.",
    )

    # --- Social & social determinants ---
    social_isolation: Literal["yes", "no", "unclear"] = Field(
        description="Whether the note suggests social isolation or loneliness."
    )
    caregiver_availability: str = Field(
        description="Who provides support, how often, and any gaps. "
        "Use 'none mentioned' if absent."
    )
    social_determinants: list[str] = Field(
        default_factory=list,
        description="Non-medical factors affecting wellbeing: financial strain, "
        "food insecurity, housing quality, transportation access, utility "
        "affordability. Empty list if none mentioned.",
    )

    # --- Services & follow-up (research-relevant) ---
    referrals_or_services: list[str] = Field(
            default_factory=list,
            description="Services in place, offered, or discussed — including any the "
            "participant DECLINED. Always capture declined offers explicitly. "
            "Format each as 'accepted/declined/in place: <service>'. "
            "Examples: 'declined: meal delivery', 'accepted: utility assistance info', "
            "'in place: home health aide 3x/week'. Empty list if none.",
    )
    follow_up_priority: Literal["routine", "elevated", "urgent"] = Field(
        description="Overall priority for follow-up implied by the note's concerns."
    )

    # --- Free-form catch-all ---
    other_notable: list[str] = Field(
        default_factory=list,
        description="Anything clinically or socially significant not captured above.",
    )