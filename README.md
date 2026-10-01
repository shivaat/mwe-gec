# mwe-gec
This is the repository for processing scripts, releases, and publication resources for the MWE-GEC dataset released with the paper "Mind the Phrase: Annotation and Identification of Multiword Expressions in Grammatical Error Correction" accepted for EMNLP 2026 Findings.

The dataset can be downloaded at https://researchdatasets.cambridge.org/datasets/mwe-gec-annotation.

## Dataste Info

The dataset contains the annotation of 1,850 corrected English essays for Multiword Expressions (MWEs). The essays and their corrections are a sample from bigger grammatical error correction (GEC) datasets that have already been publicly released for research use as part of the BEA Shared Task 2019 (Bryant et al., 2019) and the Write & Improve Corpus 2024 (Nicholls et al., 2024). We engaged expert annotators to mark up MWEs in the corrected versions of the texts, in order to rigorously analyse how learners of different proficiency levels use MWEs in their writing and how well GEC systems correct erroneous MWE usage. This also provides researchers with a new and sizeable MWE-annotated dataset. Annotation is performed using comprehensive guidelines following previous work (Savary et al., 2023; Schneider et al. 2014). 

Training data include 700 essays from [BEA 2019 training data](https://www.cl.cam.ac.uk/research/nl/bea2019st/#data) and 700 essays from [W&I Corpus 2024](https://researchdatasets.cambridge.org/datasets/write-and-improve-corpus-2024). The development data is the exact **BEA 2019 dev set** available at https://www.cl.cam.ac.uk/research/nl/bea2019st/#dain including 350 essays which are split into different CEFR levels (A, B, C) and native speakers (N). They are annotated by two annotators for MWEs. MWE tagging is in BIO format where the tags _[B-X] and _[I-X] attached to the tokens represent the beginning and the continuation of an MWE, respectively. The tag X depicts that the MWE type is not available in the annotated corpus. This repository provides scripts for automatic categorisation of MWE types or for converting the .txt files to PARSEME conllu format.

## To Be added:
- script for adding MWE errors as a new error type in ERRANT m2 files
- scripts for MWE type classification
- scripts for converting the MWE-annotated texts files to PARSEME conllu format

## Citation

```bibtex
@inproceedings{mwe-gec,
  author = {Shiva Taslimipoor and Christopher Bryant and Zheng Yuan and Diane Nicholls and Andrew Caines and Paula Buttery},
  year = {2026},
  title = {Mind the Phrase: Annotation and Identification of Multiword Expressions in Grammatical Error Correction},
  booktitle = {Findings of the Association for Computational Linguistics: EMNLP 2026},
  publisher = {Association for Computational Linguistics},
  url = {https://aclanthology.org/}
}


