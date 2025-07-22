## Setup Instructions for LanceDB_NatGeo

### 1. Install `uv` (Python package manager)

Open your terminal and run:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone the Repository
If you have Git installed, go to the directory in which you want the github repo & run:

```bash
git clone https://github.com/SiyaKamboj/LanceDB_NatGeo.git
```
If you do not have Git installed, you can download the directory as a ZIP file and unzip it manually.

### 3. Open the Project in Visual Studio Code
Open the LanceDB_NatGeo folder using Visual Studio Code.

### 4. Sync the environment
Open your terminal in the project root (inside LanceDB_NatGeo) and type:

```bash
uv sync
```
This will install all the necessary dependencies.

### 5. Move your audio files
Move your audio files into the LanceDB_NatGeo directory. These will be used by the notebook to populate LanceDB.

### 6. Launch the Notebook
Open insert_mus_into_LanceDB.ipynb in VS Code. This is called a Jupyter Notebook. 

When prompted to select a kernel on the top right, choose the one from this venv. It should be called "uv-venv-music"

### 7. Run the Code
You can now execute each code block by clicking the ▶️ play button in the top-left corner of each cell.

In each cell, I have placed some comments describing what the code is doing, but I have also placed some comments, starting with "#NOTE To Muha:" containing important information that should be read before executing the code block. 








