# YouTube Trend Analysis with CrewAI and BrightData

## Overview
This project leverages CrewAI and BrightData to analyze YouTube trends. The goal is to gather insights from YouTube videos and channels to understand trending topics, viewer engagement, and content performance.

## Features
- **Data Collection**: Use BrightData to scrape YouTube data.
- **Data Analysis**: Utilize CrewAI for analyzing video trends and viewer engagement.
- **Visualization**: Generate visual reports to present the analysis results.

## Installation
1. Clone the repository:
    ```bash
    git clone https://github.com/axeltanjung/multiagent_youtube_video_analyst.git
    cd multiagent_youtube_video_analyst
    ```
2. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage
1. Configure your BrightData and CrewAI API keys in the `config.json` file.
2. Run the data collection script:
    ```bash
    python collect_data.py
    ```
3. Analyze the collected data:
    ```bash
    python analyze_data.py
    ```
4. Generate visual reports:
    ```bash
    python generate_reports.py
    ```

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact
For any questions or inquiries, please contact [yourname@example.com](mailto:yourname@example.com).
