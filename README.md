# Ticketmastery: Classifying Rice University Maintenance Requests


## About

At Rice, the Facilities and Capital Planning (F&CP) department handles maintenance, custodial, grounds, project management, and utility operation. F&CP performs preventative maintenance for assets around campus, and is also responsible for Rice's ticketing system, a resource for students, faculty, and Rice employees who notice an issue with a space on campus. All maintenance work is documented through 'tickets' (aka work orders). A ticket might describe preventative work for an HVAC system, or corrective work requested through an online form by an undergraduate student due to an electrical problem in their dorm or residential college, for instance.

### Objectives

In coordination with our sponsors at FC\&P, numerous directions have been discussed and explored. As of the March 16, 2026, the Ticketmastery team has narrowed down a finalized project scope. The objectives we aim to complete upon completion of our project are:

1. Build an interactive, real-time dashboard that FC\&P can use to better understand their ticketing data, track tickets around campus, and identify potentially chronic issues in buildings across campus.
2. Uncover what properties of work order tickets are the highest drivers for 'repetitive tasks' (chronic issues). Particularly, investigate the relationship between preventative maintenance and repetitive work tasks.
3. Label tickets by 'request classes' (describing the nature of the maintenance request) based on their user-inputted descriptions and other ticket features.



## Run:

### <u>Dashboard</u>

**Note: This dashboard is not finished, and is in a WIP State. Following our "cupcake" design pipeline, the team is creating and testing panels seperately before embedding them into the dashboard overlay. The 3D map and "key-word cloud" panels for the dashboard are currently in development state — progress can be viewed in....**

To view the interactive dashboard (prototype) constructed for FC&P:

1. Open `src/dashboard/index.html` in a browser
2. Download the cleaned & anonomyzed work task data at `data/TA_data.csv`.
3. In the top panel, upload the file named `df_merged_tickets_assets`
4. Click "reload dashboard" to populate dashboard panels with the work task data.

REMEMBER TO RE-DOWNLOAD CLEANED MERGED TICKETS ASSETS DATA


### Modeling & Data Exploration

Data exploration, statistical analyses, and machine learning modeling is outlined and comprehensively annotated across multiple jupyter notebooks. Note that running these notebooks from the beginning will require the raw work order and locational data, which contains private information such as email addresses and phone numbers and thus is not made available in the repository. Nevertheless, all analyses can be followed by opening the Jupyter Notebooks and viewing their cell output in github or by cloning/forking the repository. Moreover, all necessary and important *cleaned* datasets, are available in the `data` folder at the root of this repository.

#### 1. Data Exploration (`src/data-exploration/`)


- **`peliminary_data_exploration.ipynb`:** A deep dive into the work order datasets provided by FC&P is provided in `preliminary\_data\_exploration.ipynb`. Work task data, asset data, and survey data are matched, features are analyzed, and plans for modeling are developed.

- **`repetitive_assets.ipynb`:** Our initial detection methodology for detecting 'repetitive tasks' (chronic issues on campus that are not fixed despite persistent work orders) is implemented and conclusions are drawn. We find that using the ASSET_ID feature is not suitable for matching corrective tickets with similar requests, and the necessity for a new strategy is discussed.

- **`repetitive_objects.ipynb`:** Our revised and improved detection methodology for detecting 'repetitive tasks.' Rather than using ASSET_IDs, corrective tickets are grouped by the broken "object" they are likely to reference using the SPACE, FLOOR, BUILDING, and SERVICE_REQUEST_CLASS features. Entries of the original dataset without space information (tickets that do not reference a specific space within a building) are dropped for the sake of this analysis, but we are still left with over 120,000 obeservations to work with — enough to perform robust analysis. We find that this so-called "Object ID" detection strategy provides much more believable results than the implementation using Asset IDs in `repetitive_assets.ipynb` since the distribution of implied object failure rates more closely follows a Power Law.

- **`ticket_heat_map.ipynb`:** ...


#### 2. Modeling (`src/modeling/`)

- **`repetitive_task_prediction.ipynb`:** Random forests and XGBoost models are experimented with, in order to predict whether a given ticket is likely to reference a chronic building issue ('repetitive ticket'). SMOTE and Threshold tuning are implemented due to the inbalanced classes (18.6:1 ratio of repetitive to non-repetitive tickets), which increase the accuracy of the XGBoost model significantly. The models accurately predict non-repetitive tickets; however, due to the unbalanced data and lack of important information in the features used for training the models are only able to reach a maximum of 46% accuracy in correctly classifying a repetitive ticket as repetitive. We plan to leverage user-defined description data by adding a "keywords" feature to improve the accuracy of these classification models.

- **`request_class_classification.ipynb`:** A random forest model was implemented to predict which of 400 request classes (describing the type of maintenance request) a ticket calls for. 


*This project was completed for the Rice Univerisity Data Science Capstone Project (Spring 2026)*