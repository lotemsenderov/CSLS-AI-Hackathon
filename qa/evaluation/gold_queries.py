"""Hand-labeled (query, expected_field, expected_keywords) gold set used to
score search.py's TF-IDF ranking against something other than itself.

Queries are paraphrases of each conference's `topics` text, not substrings of
it — copying the exact wording would let a trivial keyword-overlap ranker
score perfectly and tell us nothing about ranking quality.

Note on class balance: data/conferences.json is ~80% "Machine Learning" (the
scraper only covers ML/AI — see backend/scraper.py); Biophysics, Chemistry,
Neuroscience, and Computational Biology together make up the rest. That skew
is deliberate context for relevance_eval.py: field-match precision on an ML
query is cheap to get right by base rate alone, so it's a weak signal.
Field-match precision on a query from one of the smaller fields is a strong
signal — ranking one into the top 5 only happens if TF-IDF is actually
working. ML queries are scored on keyword-hit rate instead, against the
conference's own subfield tag (computer vision, robotics, ...).
"""

RARE_FIELD_QUERIES = [
    {
        "query": "I study how proteins fold and interact with cell membranes",
        "expected_field": "Biophysics",
        "expected_keywords": ["protein", "membrane"],
    },
    {
        "query": "using cryo-electron microscopy to resolve ion channel structures",
        "expected_field": "Biophysics",
        "expected_keywords": ["cryo-electron microscopy", "ion channels"],
    },
    {
        "query": "molecular motors, ATP synthase, and enzyme kinetics",
        "expected_field": "Biophysics",
        "expected_keywords": ["molecular motors"],
    },
    {
        "query": "NMR spectroscopy of protein-protein interactions",
        "expected_field": "Biophysics",
        "expected_keywords": ["nmr", "protein-protein"],
    },
    {
        "query": "single-molecule FRET and optical tweezers imaging",
        "expected_field": "Biophysics",
        "expected_keywords": ["fret", "optical tweezers"],
    },
    {
        "query": "using X-ray crystallography to determine macromolecular structures",
        "expected_field": "Biophysics",
        "expected_keywords": ["x-ray crystallography", "structural biology"],
    },
    {
        "query": "genome assembly and sequence alignment algorithms in bioinformatics",
        "expected_field": "Computational Biology",
        "expected_keywords": ["bioinformatics", "sequence alignment", "genome assembly"],
    },
    {
        "query": "network models and gene regulatory systems in quantitative biology",
        "expected_field": "Computational Biology",
        "expected_keywords": ["systems biology", "gene regulatory networks"],
    },
    {
        "query": "profiling gene expression in individual cells at scale",
        "expected_field": "Computational Biology",
        "expected_keywords": ["single-cell rna sequencing", "single-cell genomics"],
    },
    {
        "query": "mapping gene expression patterns across tissue sections in situ",
        "expected_field": "Computational Biology",
        "expected_keywords": ["spatial transcriptomics", "spatial genomics"],
    },
    {
        "query": "using a blood test to detect circulating tumor DNA noninvasively",
        "expected_field": "Computational Biology",
        "expected_keywords": ["cell-free dna", "liquid biopsy", "ctdna"],
    },
    {
        "query": "organic synthesis and catalysis for making new materials",
        "expected_field": "Chemistry",
        "expected_keywords": ["organic synthesis", "catalysis"],
    },
    {
        "query": "sustainable green chemistry using renewable feedstocks",
        "expected_field": "Chemistry",
        "expected_keywords": ["green chemistry", "renewable feedstocks"],
    },
    {
        "query": "computational modeling of reaction mechanisms and kinetics",
        "expected_field": "Chemistry",
        "expected_keywords": ["reaction mechanisms", "kinetics"],
    },
    {
        "query": "nanomaterials for energy storage and self-assembly",
        "expected_field": "Chemistry",
        "expected_keywords": ["nanomaterials", "energy storage"],
    },
    {
        "query": "battery materials and electrocatalysis for fuel cells",
        "expected_field": "Chemistry",
        "expected_keywords": ["battery materials", "electrocatalysis"],
    },
    {
        "query": "synaptic plasticity and how neural circuits rewire",
        "expected_field": "Neuroscience",
        "expected_keywords": ["synaptic plasticity", "neural circuits"],
    },
    {
        "query": "computational models of neurodevelopment and glial cells",
        "expected_field": "Neuroscience",
        "expected_keywords": ["computational neuroscience", "glial biology"],
    },
    {
        "query": "fMRI studies of memory and decision making in the brain",
        "expected_field": "Neuroscience",
        "expected_keywords": ["fmri", "memory"],
    },
    {
        "query": "spiking neural network models of brain circuits",
        "expected_field": "Neuroscience",
        "expected_keywords": ["spiking neural networks", "brain modeling"],
    },
    {
        "query": "Alzheimer's disease biomarkers and neurodegeneration",
        "expected_field": "Neuroscience",
        "expected_keywords": ["alzheimer", "neurodegeneration"],
    },
]

# Machine Learning subfields: field-match precision is a weak signal here
# (base rate ~93%), so these are scored on subfield-tag keyword hits instead.
ML_SUBFIELD_QUERIES = [
    {
        "query": "object detection and image recognition with deep networks",
        "expected_field": "Machine Learning",
        "expected_keywords": ["computer vision"],
    },
    {
        "query": "natural language processing for text understanding",
        "expected_field": "Machine Learning",
        "expected_keywords": ["natural language processing"],
    },
    {
        "query": "autonomous robot navigation and manipulation",
        "expected_field": "Machine Learning",
        "expected_keywords": ["robotics"],
    },
    {
        "query": "mining large datasets to find patterns",
        "expected_field": "Machine Learning",
        "expected_keywords": ["data mining"],
    },
    {
        "query": "speech and audio signal processing",
        "expected_field": "Machine Learning",
        "expected_keywords": ["signal processing"],
    },
]

ALL_QUERIES = RARE_FIELD_QUERIES + ML_SUBFIELD_QUERIES