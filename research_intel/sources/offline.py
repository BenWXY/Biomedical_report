from __future__ import annotations

from research_intel.models import PublicationRecord, SourceResult, TrialRecord
from research_intel.sources.base import DataSource


class OfflineDemoSource(DataSource):
    name = "Offline demo fixtures"

    def fetch(self, target: str) -> SourceResult:
        normalized = target.strip().upper()
        if normalized not in {"HER2", "ERBB2"}:
            return SourceResult(
                self.name,
                self._generic_records(target),
                [f"Offline fixture is optimized for HER2; generated representative records for {target}."],
            )
        return SourceResult(self.name, self._her2_records())

    def _her2_records(self):
        return [
            TrialRecord(
                nct_id="NCT00000001",
                title="Trastuzumab deruxtecan in HER2-positive metastatic breast cancer",
                sponsor="AstraZeneca / Daiichi Sankyo",
                phase="PHASE3",
                status="RECRUITING",
                enrollment=980,
                interventions=["Trastuzumab deruxtecan", "Investigator choice chemotherapy"],
                countries=["United States", "Japan", "Spain", "China"],
                start_date="2024-02",
                completion_date="2028-09",
                url="https://clinicaltrials.gov/study/NCT00000001",
            ),
            TrialRecord(
                nct_id="NCT00000002",
                title="Tucatinib combination therapy for HER2-positive colorectal cancer",
                sponsor="Seagen",
                phase="PHASE2",
                status="ACTIVE_NOT_RECRUITING",
                enrollment=240,
                interventions=["Tucatinib", "Trastuzumab"],
                countries=["United States", "France", "Germany"],
                start_date="2023-05",
                completion_date="2026-12",
                url="https://clinicaltrials.gov/study/NCT00000002",
            ),
            TrialRecord(
                nct_id="NCT00000003",
                title="Zanidatamab in HER2-amplified biliary tract cancer",
                sponsor="Jazz Pharmaceuticals",
                phase="PHASE2",
                status="COMPLETED",
                enrollment=87,
                interventions=["Zanidatamab"],
                countries=["United States", "South Korea"],
                start_date="2021-08",
                completion_date="2024-01",
                url="https://clinicaltrials.gov/study/NCT00000003",
            ),
            PublicationRecord(
                pmid="10000001",
                title="Antibody-drug conjugates reshape treatment of HER2-positive solid tumors",
                authors=["Smith J", "Chen Y", "Garcia M"],
                journal="Journal of Clinical Oncology",
                publication_date="2025 Jan",
                abstract="Review of HER2-directed ADC efficacy, resistance mechanisms, and sequencing strategies.",
                keywords=["HER2", "ADC", "breast cancer"],
                url="https://pubmed.ncbi.nlm.nih.gov/10000001/",
            ),
            PublicationRecord(
                pmid="10000002",
                title="HER2-low disease biology and clinical implications across tumor types",
                authors=["Wang L", "Patel R"],
                journal="Nature Reviews Clinical Oncology",
                publication_date="2024 Nov",
                abstract="HER2-low expression creates broader patient segmentation and diagnostic challenges.",
                keywords=["HER2-low", "biomarker", "solid tumors"],
                url="https://pubmed.ncbi.nlm.nih.gov/10000002/",
            ),
        ]

    def _generic_records(self, target: str):
        return [
            TrialRecord(
                nct_id="DEMO-TRIAL-001",
                title=f"Representative phase 2 study for {target}",
                sponsor="Demo Biopharma",
                phase="PHASE2",
                status="RECRUITING",
                enrollment=120,
                interventions=[f"{target} targeted therapy"],
                countries=["United States"],
            ),
            PublicationRecord(
                pmid="DEMO-PMID-001",
                title=f"Recent translational research progress for {target}",
                authors=["Demo A"],
                journal="Demo Medical Journal",
                publication_date="2025",
                abstract=f"Representative publication describing {target} biology and clinical strategy.",
                keywords=[target],
            ),
        ]

