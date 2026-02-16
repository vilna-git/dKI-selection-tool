# dKI Scheme Selection Tool

A Python-based MCDA tool for choosing optimal dKI schemes based on organizational requirements for non-tech users.

## Overview

This project implements a  decision tree with **7+ million distinct pathways** to help organizations choose the most appropriate dKI scheme from six options:

1. **PKI with Certificate Authority**
2. **Identity-Based Encryption (IBE)**
3. **Zero-Trust Architecture**
4. **Self-Sovereign Identity (SSI)**
5. **Peer-to-Peer Web-of-Trust**
6. **Decentralized PKI / Blockchain**

## Main Features
- **Dual Interface Support**
  - Standalone HTML web application
  - Command-line Python interface for automation

- **Three-Stage Assessment**
  - Stage 1: Criteria ranking (Security, Performance, Software Maturity, Infrastructure Complexity, O&M Complexity)
  - Stage 2: Organizational context questions (IT capability, scale requirements, regulatory compliance)
  - Stage 3: Nine clarifying questions (yes,no,idk) with dynamic scoring adjustments

- **Scoring System**
  - Baseline criteria scores for each scheme
  - Dynamic adjustments based on user responses to questions
  - 4 weighting schemes
  - Inverted scoring for negative criteria (complexity metrics)

- **Monte Carlo Check**
  - Simulation framework with multiple random trials
  - Statistical analysis of scheme selection distributions
  - Weighting pattern verification

## Technical Implementation

### Core Components

- **`assessment.py`**: Main assessment interface with user interaction
- **`montecarlo.py`**: Monte Carlo simulation
- **JSON Configuration Files**:
  - `schemes.json`: Scheme names and metadata
  - `criteria.json`: Assessment criteria definitions
  - `weightings.json`: Four weighting schemes
  - `baseline_scheme_scores.json`: Initial scheme ratings
  - `stage3_questions.json`: Clarifying questions with scoring adjustments
### Decision Logic

```
Final Score = Σ (adjusted_score × weight × criterion_direction)

where:
- adjusted_score: baseline ± stage3 adjustments (bounded 1-6)
- weight: selected from 4 contextual schemes
- criterion_direction: +1 for positive criteria (A,B,C), -1 for negative (D,E)
```

## Getting Started


### Options to Use

**Option1: Web Interface (Recommended)** 
- Open `index.html` in any browser
- No installation required!
- Instant results with downloadable JSON export

**Option 2: Command Line Interface**
- Python 3.8 or higher required
- No external dependencies (uses only standard library)

### Installation

```bash
git clone https://github.com/vilna-git/dKI-selection-tool.git
cd dKI-selection-tool

# For web interface: just open index.html in your browser
```
No additional installation required


### Usage

#### Web Interface (Easiest)

Just open `index.html` in your browser and follow the interactive wizard

#### Run Interactive Assessment

```bash
python3 assessment.py
```

Follow the prompts through three stages:
1. Rank criteria importance (1-5, each used once)
2. Answer organizational context questions (y/n)
3. Answer refinement questions (y/n/not sure - max 2 "not sure")

#### Run Monte Carlo Simulation

```bash
# Default 1000 trials
python3 montecarlo.py

# Custom trial count
python3 montecarlo.py --trials 5000
```
## Validation Results

Monte Carlo simulation with 1000 trials:
- **Weighting distribution**: W0(12.5%), W1(12.5%), W2(25%), W3(50%)
- **Pad wastage bound**: O(d) ≤ W(n,d) ≤ 0.2n + O(d)
- **All schemes selected**: Validates decision tree balance

---

**Note**: This project gives recommendations based on configurable criteria. Organizations must conduct thorough security assessments before deploying any dKI scheme in production environments.

