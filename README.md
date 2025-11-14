# LIBRO Replication Study

Replication of "Large Language Models are Few-shot Testers" under constrained settings.

## Setup

### 1. Install Defects4J v3.0
```bash
git clone https://github.com/rjust/defects4j.git
cd defects4j
git checkout v3.0.0
./init.sh
export PATH=$PATH:$(pwd)/framework/bin
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure HuggingFace Access
```bash
huggingface-cli login
```

## Project Structure
```
libro_replication/
├── config/              # Configuration files
├── data/               # Bug data and metadata
├── src/
│   ├── core/          # Core pipeline components
│   ├── utils/         # Utility functions
│   └── evaluation/    # Evaluation metrics
├── scripts/           # Standalone scripts
├── notebooks/         # Jupyter/Colab notebooks
├── tests/             # Unit tests
├── logs/              # Log files
└── results/           # Experimental results
```

## Usage

### Run Pipeline on Single Bug
```python
from src.libro_pipeline import LIBROPipeline

pipeline = LIBROPipeline()
pipeline.load_model("starcoder2-15b")

bug_info = {
    "project": "Lang",
    "bug_id": "1",
    "title": "Bug title",
    "description": "Bug description..."
}

results = pipeline.run_on_bug(bug_info)
print(f"BRTs found: {len(results['brt_tests'])}")
```

## Day 1 Status

✅ Defects4J v3.0 installed
✅ Bug selection script created
✅ Model manager implemented
✅ Pipeline skeleton completed
✅ Configuration system set up
✅ Logging infrastructure ready

## Next Steps (Day 2)
- Implement prompt engineering
- Test multi-sample generation
- Create few-shot example bank
