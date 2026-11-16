# Therapeutic intervention evidence

`TherapeuticEvidenceRecord` stores study-level evidence about an intervention. It is deliberately separate from `TherapeuticProductRecord`: product/manufacturing identity is not the same thing as evidence that a product changed a biological or clinical endpoint.

## Independent classification axes

- `evidence_class`: myocardial regeneration, myocardial repair, myocardial preservation, genetic disease modification, vascular tissue engineering, immune modulation, or other.
- `modality`: circRNA, modRNA, siRNA, ASO, AAV, gene editing, cell therapy, engineered tissue, hydrogel, small molecule, biologic, immune intervention, or other.

Do not infer one axis from the other. A modality does not establish a biological effect, and an indication does not establish a mechanism.

## Required evidence context

Records can preserve target/genotype, payload/construct, delivery, proposed mechanism, model system, species, dose, schedule, comparator, endpoint-level observations, analysis population, denominator, follow-up, subgroup analysis, multiplicity handling, safety findings, limitations, evidence IDs and a source locator.

Unknown values must remain unknown (or explicitly say "not reported" when that is the source's wording); do not fill gaps by inference. Keep each endpoint separate and preserve units, analysis set, denominator and timepoint in its endpoint object.

## Regeneration is a high bar

Cell-cycle entry (for example Ki67), DNA synthesis, increased LVEF, reduced scar, fibrosis change, graft patency, or improved symptoms are not individually proof of new cardiomyocyte formation. A regeneration claim should be supported by a convergent evidence package appropriate to the model, including direct evidence of completed division/new cardiomyocyte number and lineage where feasible, functional integration/maturation, and safety follow-up. The record schema does not automatically award a regeneration label; curation remains a scientific decision.

## Example

```python
from cardiatlas import TherapeuticEvidenceRecord

record = TherapeuticEvidenceRecord(
    id="therapeutic-evidence:study-001",
    name="Study-level intervention evidence",
    evidence_class="myocardial_repair",
    modality="modRNA",
    target_or_genotype="MYC-Cyclin T1",
    model_system="preclinical myocardial infarction model",
    endpoints=[{
        "endpoint": "LVEF",
        "measurement": "echocardiography",
        "value": "not reported",
        "units": "%",
        "timepoint": "4 weeks",
        "interpretation": "functional endpoint; not proof of regeneration",
    }],
    evidence_ids=["evidence:study-001"],
    source_locator={"source_id": "PMID:...", "section": "Results"},
)
```

These are research metadata contracts, not a clinical decision-support system, regulatory determination, or efficacy ranking.
