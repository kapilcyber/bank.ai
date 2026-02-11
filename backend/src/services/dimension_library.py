"""
Backend-controlled Dimension Library for JD/Resume matching (V2).

Critical rule:
- Dimensions must come ONLY from this library. GPT is allowed to SELECT from this set,
  but must never invent new dimensions or IDs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence


@dataclass(frozen=True)
class Dimension:
    """
    A scoring dimension definition controlled by backend.

    Notes:
    - id must be stable (used as key in scoring/breakdowns and persisted/cached).
    - seed_skills are OPTIONAL hints to help extraction; scoring must not depend on them.
    """

    id: str
    label: str
    definition: str
    seed_skills: Sequence[str] = ()


def get_dimension_library() -> List[Dimension]:
    """
    Return the canonical dimension library.

    Keep this list small and general-purpose. If you need more granularity, add
    dimensions here intentionally (never via GPT).
    """

    return [
        Dimension(
            id="experience_seniority",
            label="Experience & Seniority",
            definition="Years of experience, seniority level, leadership scope, and ownership.",
            seed_skills=("lead", "architect", "mentor", "ownership", "senior", "principal"),
        ),
        Dimension(
            id="core_technical_skills",
            label="Core Technical Skills",
            definition="Core technologies and tools required for the role (primary stack).",
        ),
        Dimension(
            id="networking_protocols",
            label="Networking & Protocols",
            definition="Networking fundamentals and protocols (e.g., BGP, OSPF, VLANs, TCP/IP).",
            seed_skills=("BGP", "OSPF", "TCP/IP", "VLAN", "HSRP", "MPLS"),
        ),
        Dimension(
            id="security_technologies",
            label="Security Technologies",
            definition="Security tooling and technologies (e.g., NGFW, IDS/IPS, SIEM, WAF, Zscaler).",
            seed_skills=("NGFW", "IDS/IPS", "SIEM", "WAF", "Zscaler", "Palo Alto", "Fortinet"),
        ),
        Dimension(
            id="cloud_architecture",
            label="Cloud & Architecture",
            definition="Cloud platforms and architecture (AWS/Azure/GCP, IAM, network/security architecture).",
            seed_skills=("AWS", "Azure", "GCP", "IAM", "VPC", "Kubernetes"),
        ),
        Dimension(
            id="incident_operations",
            label="Incident & Operations",
            definition="Operations, incident response, troubleshooting, reliability, on-call, DDoS handling.",
            seed_skills=("incident", "P1", "on-call", "DDoS", "RCA", "SRE"),
        ),
        Dimension(
            id="compliance_governance",
            label="Compliance & Governance",
            definition="Regulatory/compliance frameworks and governance (ISO 27001, SOC2, PCI-DSS, SOX).",
            seed_skills=("ISO 27001", "SOC2", "PCI-DSS", "SOX", "HIPAA", "NIST"),
        ),
        Dimension(
            id="certifications",
            label="Certifications",
            definition="Professional certifications relevant to the role.",
            seed_skills=("CCNA", "CCNP", "CCIE", "AWS Certified", "CISSP", "CEH"),
        ),
        Dimension(
            id="other_relevant",
            label="Other Relevant Requirements",
            definition="Any JD requirements that don't fit well into other dimensions, still from the library.",
        ),
    ]


def dimension_library_as_dict(dimensions: Sequence[Dimension]) -> Dict[str, Dimension]:
    """Convenience lookup by id."""
    return {d.id: d for d in dimensions}



