# Ticketmastery: Analyzing Service Tickets to Better Serve Rice

![Showcase Poster](src/assets/Showcase-Poster.svg)

## About

At Rice, the Facilities and Capital Planning (F&CP) department handles maintenance, custodial, grounds, project management, and utility operation. F&CP performs preventative maintenance for assets around campus, and is also responsible for Rice's ticketing system, a resource for students, faculty, and Rice employees who notice an issue with a space on campus. All maintenance work is documented through 'tickets' (aka work orders). A ticket might describe preventative work for an HVAC system, or corrective work requested through an online form by an undergraduate student due to an electrical problem in their dorm or residential college, for instance.

### Objectives

In coordination with our sponsors at FC\&P, numerous directions have been discussed and explored. As of the March 16, 2026, the Ticketmastery team has narrowed down a finalized project scope. The objectives we aim to complete upon completion of our project are:

1. Build an interactive, real-time dashboard that FC\&P can use to better understand their ticketing data, track tickets around campus, and identify potentially chronic issues in buildings across campus.
2. Uncover what properties of work order tickets are the highest drivers for 'repetitive tasks' (chronic issues). Particularly, investigate the relationship between preventative maintenance and repetitive work tasks.
3. Label tickets by 'request classes' (describing the nature of the maintenance request) based on their user-inputted descriptions and other ticket features.



## Run:

### Dashboard

TicketMastery is a Streamlit dashboard built to help Rice FE&P staff explore work task data across repeated maintenance issues, campus locations, ticket sentiment, and common keywords.

The current dashboard entry point is:

```text
src/Streamlit/StreamlitApp.py
```

## Running Locally

To run the dashboard locally, the required CSV files must exist in the project’s `data/` folder:

```text
data/
├── V_OM_WORK_TASK.csv
├── V_OM_WORK_TASK_ASSET.csv
├── V_SPACE_DETAIL.csv
├── TICKETS_WITH_COORDS.csv
└── V_OM_WORK_TASK_SURVEY.csv
```

These files are not included in the repository for privacy and data security reasons.

Install the required dependencies using the Streamlit requirements file:

```bash
pip install -r src/Streamlit/requirements_streamlit_dashboard.txt
```

Then run the dashboard:

```bash
streamlit run src/Streamlit/StreamlitApp.py
```

The app supports local CSV-based development and Snowflake-based deployment. Locally, it loads from the `data/` folder. In Snowflake, it is intended to connect to Snowflake-hosted views.

## Panels

### Panel 1: Repetitive Tasks

Identifies recurring work task patterns that may indicate unresolved or repeated maintenance issues. Users can adjust the time window, minimum day threshold, and filtering options to focus on likely repetitive corrective tickets.

### Panel 2: Map

Displays ticket activity across campus using building coordinate data. Users can filter by date range, keyword, service class, task type, task priority, and building-related fields.

### Panel 3: Sentiment Analysis

Scores ticket-related text fields and highlights the strongest positive and negative examples. Supported fields include request descriptions, resolution notes, and customer response comments.

### Panel 4: Keyword Search + Word Cloud

Shows common words in ticket descriptions and supports keyword filtering, grouping by fields such as `SERVICE_CLASS`, `REQUEST_CLASS`, and `RESPONSIBLE_ORGANIZATION_NAME`, and viewing the matching tickets behind the results.

## Snowflake Deployment

The dashboard is deployed as a Streamlit app in the sponsor’s Snowflake environment. FE&P staff with the appropriate internal access should be able to use the live Snowflake version.


### Modeling & Data Exploration

Data exploration, statistical analyses, and machine learning modeling is outlined and comprehensively annotated across multiple jupyter notebooks. Note that running these notebooks from the beginning will require the raw work order and locational data, which contains private information such as email addresses and phone numbers and thus is not made available in the repository. Nevertheless, all analyses can be followed by opening the Jupyter Notebooks and viewing their cell output in github or by cloning/forking the repository. Moreover, all necessary and important *cleaned* datasets, are available in the `data` folder at the root of this repository.

#### 1. Data Exploration (`src/data-exploration/`)

- **`preliminary_data_exploration.ipynb`:** A deep dive into the work order datasets provided by FC&P is provided in `preliminary\_data\_exploration.ipynb`. Work task data, asset data, and survey data are matched, features are analyzed, and plans for modeling are developed.

- **`repetitive_assets.ipynb`:** Our initial detection methodology for detecting 'repetitive tasks' (chronic issues on campus that are not fixed despite persistent work orders) is implemented and conclusions are drawn. We find that using the ASSET_ID feature is not suitable for matching corrective tickets with similar requests, and the necessity for a new strategy is discussed.

- **`repetitive_objects.ipynb`:** Our revised and improved detection methodology for detecting 'repetitive tasks.' Rather than using ASSET_IDs, corrective tickets are grouped by the broken "object" they are likely to reference using the SPACE, FLOOR, BUILDING, and SERVICE_REQUEST_CLASS features. Entries of the original dataset without space information (tickets that do not reference a specific space within a building) are dropped for the sake of this analysis, but we are still left with over 120,000 observations to work with — enough to perform robust analysis. We find that this so-called "Object ID" detection strategy provides much more believable results than the implementation using Asset IDs in `repetitive_assets.ipynb` since the distribution of implied object failure rates more closely follows a Power Law.

- **`ticket_heat_map.ipynb`:** This map code merges the two datasets into one and maps tickets to their respective location on the Rice campus. The map also accounts for the number of tickets at each location, with a corresponding height and color for each location. The higher and warmer the color, the larger the number of tickets. To run this code, one must install pandas for data handling and manipulation and pydeck for map plotting. In the full interactive map, one must also install Streamlit. Additionally, one can see the breakdown of tickets by building class to see which classes need more attention compared to others (note that this is overall tickets and is not normalized with respect to the number of buildings per class).

- **`description_analysis.ipynb`:** Analyzes description data and builds the sentiment score features utilized in our logistic regression model (see `src/modeling/repetitive_task_inference`). Particularly, we explore the three text fields in the work task data — `DESCRIPTION` (written by the requester at submission), `RESOLUTION_DESCRIPTION` (written by the technician at completion), and `RESPONSE_COMMENTS` (collected from post-completion surveys). Tickets, assets, and surveys are joined on `WORK_TASK_ID` (with assets and surveys deduplicated to one row per ticket), then narrowed to a working set of 24 columns. We approach the text from two angles. First, we score each field with VADER (a lexicon-based sentiment model well suited to short, informal text), assigning each ticket a compound score from -1.0 to +1.0. Second, we tokenize the `DESCRIPTION` field (lowercasing, stripping punctuation and digits, removing stopwords) and compute keyword frequencies grouped by `REQUEST_CLASS` and `SERVICE_CLASS`, then convert raw counts into a per-class appearance rate (the share of distinct tickets in each class containing a keyword at least once) so the signal is comparable across classes of very different sizes. Outputs include both the per-ticket sentiment columns — fed into `repetitive_task_inference.ipynb` as features — and CSVs of overall, per-class, and per-organization keyword frequencies that power the dashboard's Keyword Search and Word Cloud panel.

#### 2. Modeling (`src/modeling/`)

- **`repetitive_task_inference.ipynb`:** Our primary inferential model identifying which ticket features drive an "Object" to be flagged as repetitive. This is the notebook that finally completes our first Objective, and describes which features contribute to repetitive building issues on Rice's campus. Using the Object-ID labels from `repetitive_objects.ipynb`, we fit an unregularized logistic regression (via `statsmodels.Logit`) on all 100,965 corrective tickets, with creatively engineered features including building condition (FCI), preventive-maintenance coverage at the space level, first-floor flag, ticket asset count, description sentiment, completion within FEP's 19-day SLA, and one-hot encoded service class, organization, day-of-week, and month-of-year fixed effects. Categorical fields use `drop_first=True` to avoid the dummy-variable trap, and predictors with VIF > 10 are pruned to keep coefficient estimates stable. Because the goal is inference (not prediction), the model is fit on the full sample and its per-feature odds ratios are read directly: first-floor tickets are ~2.25× more likely to recur, spaces with preventive maintenance have ~61% lower odds of recurrence, and tickets closed within FEP's 19-day SLA are no more likely to recur than late closures — reassuring evidence that technicians are not gaming the SLA window.

- **`repetitive_task_prediction.ipynb`:** *This notebook was part of a previous iteration of the project, and is now deprecated in lieu of `repetitive_task_inference.ipynb` due to low accuracy and subpar model interpretability. This notebook is kept for reference, but was not employed in our final analysis.* Random forests and XGBoost models are experimented with, in order to predict whether a given ticket is likely to reference a chronic building issue ('repetitive ticket'). SMOTE and Threshold tuning are implemented due to the inbalanced classes (18.6:1 ratio of repetitive to non-repetitive tickets), which increase the accuracy of the XGBoost model significantly. The models accurately predict non-repetitive tickets; however, due to the unbalanced data and lack of important information in the features used for training the models are only able to reach a maximum of 46% accuracy in correctly classifying a repetitive ticket as repetitive.

- **`request_class_cluster.ipynb`:** Evaluates two clustering methodologies aimed at reducing the operational complexity of a request system containing 400 overly granular classes. By leveraging semantic similarity within the REQUEST_CLASS and DESCRIPTION fields, the goal was to streamline reporting by consolidating these entries into 100 cohesive groups. While both K-Means and Agglomerative approaches were tested, the Agglomerative model proved superior for this use case. Unlike the K-Means model, which failed to identify an optimal cluster count via the elbow method, the Agglomerative approach provided a deterministic framework that captured the natural hierarchy of maintenance tasks. Ultimately, the use of a dendrogram enabled a more intuitive, data-driven selection of the final 100 clusters, significantly improving operational efficiency compared to the rigid, predefined constraints of the K-Means method.




*This project was completed for the Rice University Data Science Capstone Project (Spring 2026)*
