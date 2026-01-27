# RippleGUItester: Change-Aware Exploratory Testing

RippleGUItester is a **change-driven exploratory GUI testing system**.  
It treats a code change as the epicenter of a *ripple effect* and systematically explores its broader, user-visible impacts through the graphical user interface (GUI).

---

## Data Crawling, Preparation, and Artifacts

RippleGUItester is a general change-aware exploratory testing approach.  
The software systems listed below are used **only to evaluate the approach**, and do not limit its general applicability.

---

## Data Crawling and Scenario Knowledge Base (SKB) Construction

### Firefox (Mozilla Bugzilla & Mercurial)

#### 1. Crawl Bug Reports for SKB Construction

Historical bug reports are crawled from **Mozilla Bugzilla** to construct the Scenario Knowledge Base (SKB).

- Scripts: `scripts/0_0` – `scripts/0_3`
- Target project: **Firefox**

#### 2. Crawl Pull Requests for Testing

Pull requests used as testing subjects are crawled using:

- Scripts: `scripts/1_0` – `scripts/1_3`

#### 3. SKB Construction Pipeline

The SKB is generated using the following pipeline:

- Scripts: `scripts/2_0` – `scripts/2_6`

---

### Software Under Test (SUTs) on GitHub

The following GitHub-hosted systems are used as SUTs:

- **Zettlr**
- **JabRef**
- **Godot**

#### 4. Crawl Issues and Pull Requests for SKB Construction

Issues and pull requests are crawled from GitHub to build the SKB:

- Scripts: `scripts/3_0` – `scripts/3_7`

#### 5. Crawl Pull Requests for Testing

Pull requests used as testing subjects are collected using:

- Scripts: `scripts/4_0` – `scripts/4_8`

#### 6. SKB Construction Pipeline

The SKB is constructed using the following scripts:

- Scripts: `scripts/5_0` – `scripts/5_7`

---

## Running RippleGUItester

To execute RippleGUItester on the collected pull requests:

1. Start the Docker environment (ensure the Docker daemon is running).

2. Run RippleGUItester:

```bash
python scripts/app.py
```

3. Filter bug reports:

```bash
python scripts/post_process_bug_reports.py
```

---

## Reported Bugs

The following real-world bugs were discovered and reported by RippleGUItester:

| No. | Project | Bug ID / Link                                                                                                |
| --: | ------- | ------------------------------------------------------------------------------------------------------------ |
|   1 | Zettlr  | [https://github.com/Zettlr/Zettlr/issues/6067](https://github.com/Zettlr/Zettlr/issues/6067)                 |
|   2 | Zettlr  | [https://github.com/Zettlr/Zettlr/issues/6090](https://github.com/Zettlr/Zettlr/issues/6090)                 |
|   3 | Zettlr  | [https://github.com/Zettlr/Zettlr/issues/6091](https://github.com/Zettlr/Zettlr/issues/6091)                 |
|   4 | Zettlr  | [https://github.com/Zettlr/Zettlr/issues/6092](https://github.com/Zettlr/Zettlr/issues/6092)                 |
|   5 | Zettlr  | [https://github.com/Zettlr/Zettlr/issues/6093](https://github.com/Zettlr/Zettlr/issues/6093)                 |
|   6 | Zettlr  | [https://github.com/Zettlr/Zettlr/issues/6099](https://github.com/Zettlr/Zettlr/issues/6099)                 |
|   7 | Zettlr  | [https://github.com/Zettlr/Zettlr/issues/6101](https://github.com/Zettlr/Zettlr/issues/6101)                 |
|   8 | Zettlr  | [https://github.com/Zettlr/Zettlr/issues/6102](https://github.com/Zettlr/Zettlr/issues/6102)                 |
|   9 | Zettlr  | [https://github.com/Zettlr/Zettlr/issues/6103](https://github.com/Zettlr/Zettlr/issues/6103)                 |
|  10 | Zettlr  | [https://github.com/Zettlr/Zettlr/issues/6104](https://github.com/Zettlr/Zettlr/issues/6104)                 |
|  11 | Zettlr  | [https://github.com/Zettlr/Zettlr/issues/6106](https://github.com/Zettlr/Zettlr/issues/6106)                 |
|  12 | Zettlr  | [https://github.com/Zettlr/Zettlr/issues/6108](https://github.com/Zettlr/Zettlr/issues/6108)                 |
|  13 | Zettlr  | [https://github.com/Zettlr/Zettlr/issues/6109](https://github.com/Zettlr/Zettlr/issues/6109)                 |
|  14 | Zettlr  | [https://github.com/Zettlr/Zettlr/issues/6128](https://github.com/Zettlr/Zettlr/issues/6128)                 |
|  15 | Zettlr  | [https://github.com/Zettlr/Zettlr/issues/6129](https://github.com/Zettlr/Zettlr/issues/6129)                 |
|  16 | JabRef  | [https://github.com/JabRef/jabref/issues/14654](https://github.com/JabRef/jabref/issues/14654)               |
|  17 | JabRef  | [https://github.com/JabRef/jabref/issues/14789](https://github.com/JabRef/jabref/issues/14789)               |
|  18 | JabRef  | [https://github.com/JabRef/jabref/issues/14804](https://github.com/JabRef/jabref/issues/14804)               |
|  19 | JabRef  | [https://github.com/JabRef/jabref/issues/14805](https://github.com/JabRef/jabref/issues/14805)               |
|  20 | JabRef  | [https://github.com/JabRef/jabref/issues/14807](https://github.com/JabRef/jabref/issues/14807)               |
|  21 | JabRef  | [https://github.com/JabRef/jabref/issues/14821](https://github.com/JabRef/jabref/issues/14821)               |
|  22 | JabRef  | [https://github.com/JabRef/jabref/issues/14822](https://github.com/JabRef/jabref/issues/14822)               |
|  23 | Godot   | [https://github.com/godotengine/godot/issues/114157](https://github.com/godotengine/godot/issues/114157)     |
|  24 | Firefox | [https://bugzilla.mozilla.org/show_bug.cgi?id=2010360](https://bugzilla.mozilla.org/show_bug.cgi?id=2010360) |
|  25 | Firefox | [https://bugzilla.mozilla.org/show_bug.cgi?id=1986295](https://bugzilla.mozilla.org/show_bug.cgi?id=1986295) |
|  26 | Firefox | [https://bugzilla.mozilla.org/show_bug.cgi?id=1986162](https://bugzilla.mozilla.org/show_bug.cgi?id=1986162) |

---

## Data Download

The data folder contains the Scenario Knowledge Base (SKB) and the pull requests (PRs) under test.

Run the following commands to download and extract the data:

```bash
wget https://github.com/RippleTester/RippleGUITesting/releases/download/data/data.zip
unzip data.zip
```

### Folder Structure

* **`knowledge_base/`**: Bug reports, issues, and pull requests used to construct the Scenario Knowledge Base (SKB).
* **`test_pulls/`**: Pull requests for testing.

## Evaluation Download

The output folder contains the corresponding evaluation results.

Run the following commands to download and extract the data:

```bash
wget https://github.com/RippleTester/RippleGUITesting/releases/download/data/output.zip
unzip output.zip
````

### Folder structure

* **`rqN_*/`**: Labeling results for research question *RQ N*.
* **`rqN_*.txt`**: Analysis summaries corresponding to *RQ N*.



