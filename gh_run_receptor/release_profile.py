"""Defining release-profile evidence authority without external inference."""

from __future__ import annotations

from collections.abc import Collection, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any


@dataclass(frozen=True, slots=True)
class ReleaseClaimAuthority:
    """Describing the strongest assertion allowed for one release claim."""

    source: str
    maximum_assertion: str
    fallback: str | None
    subject_key: str | None = None
    successful_step_facet: str | None = None


RELEASE_CLAIM_AUTHORITIES: Mapping[str, ReleaseClaimAuthority] = MappingProxyType(
    {
        "event": ReleaseClaimAuthority(
            source="github_run_api",
            maximum_assertion="observed_source_fact",
            fallback=None,
            subject_key="event",
        ),
        "head_ref": ReleaseClaimAuthority(
            source="github_run_api",
            maximum_assertion="observed_source_fact",
            fallback=None,
            subject_key="head_ref",
        ),
        "head_sha": ReleaseClaimAuthority(
            source="github_run_api",
            maximum_assertion="observed_source_fact",
            fallback=None,
            subject_key="head_sha",
        ),
        "phase_state": ReleaseClaimAuthority(
            source="github_jobs_api_and_bounded_name_classification",
            maximum_assertion="presentation_facet_with_source_state",
            fallback=None,
        ),
        "tag_verification": ReleaseClaimAuthority(
            source="unavailable",
            maximum_assertion="not_observed",
            fallback="not_observed",
        ),
        "registry_delivery": ReleaseClaimAuthority(
            source="name_classified_workflow_step",
            maximum_assertion="step_success",
            fallback="not_observed",
            successful_step_facet="publish",
        ),
        "github_release_delivery": ReleaseClaimAuthority(
            source="unavailable",
            maximum_assertion="not_observed",
            fallback="not_observed",
        ),
        "archive_delivery": ReleaseClaimAuthority(
            source="name_classified_workflow_step",
            maximum_assertion="step_success",
            fallback="not_observed",
            successful_step_facet="archive",
        ),
        "actions_artifact_inventory": ReleaseClaimAuthority(
            source="github_artifacts_api",
            maximum_assertion="observed_inventory_only",
            fallback="not_observed",
        ),
        "external_delivery": ReleaseClaimAuthority(
            source="unavailable",
            maximum_assertion="not_observed",
            fallback="not_observed",
        ),
    }
)


def release_identity(subject: Mapping[str, Any]) -> dict[str, Any]:
    """Building release identity from declared source authorities."""
    identity = {
        key: subject.get(authority.subject_key)
        for key, authority in RELEASE_CLAIM_AUTHORITIES.items()
        if authority.subject_key is not None
    }
    identity["tag_verification"] = RELEASE_CLAIM_AUTHORITIES["tag_verification"].fallback
    return identity


def release_delivery_step_evidence(
    successful_step_facets: Collection[str],
) -> dict[str, str]:
    """Reporting workflow-step evidence without claiming external delivery."""
    states = {}
    for output_key, claim_key in (
        ("registry", "registry_delivery"),
        ("archive", "archive_delivery"),
    ):
        authority = RELEASE_CLAIM_AUTHORITIES[claim_key]
        states[output_key] = (
            "step_success"
            if authority.successful_step_facet in successful_step_facets
            else str(authority.fallback)
        )
    return states


def release_external_delivery_state() -> str:
    """Returning the strongest independent external-delivery assertion available."""
    return str(RELEASE_CLAIM_AUTHORITIES["external_delivery"].fallback)


def release_tag_display_state(state: Any) -> str:
    """Rendering the stable compact alias for tag-verification state."""
    return "unverified" if state == "not_observed" else str(state)
