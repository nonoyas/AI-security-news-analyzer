# AI-security-news-analyzer
An automated Python system leveraging AI to collect, process, and summarize weekly cybersecurity news for efficient threat intelligence and report generation.

----------------------------------------------------------------------------------------
1. Daily News Collection
Action: Automated scripts (e.g., daily_news_collector.py) retrieve the latest cybersecurity news articles from designated web sources.
Output: Daily raw news data stored in CSV format.

2. Weekly Data Processing
Action: All daily collected news data from the past week is aggregated and pre-processed. This involves deduplicating articles based on unique identifiers (e.g., URLs).
Output: A clean, consolidated weekly news report in CSV format.

3. AI-Powered Summary Generation
Action: A pre-trained AI model (specifically, the KoBART-based gogamza/kobart-base-v2 model, accessed via the Hugging Face Transformers library) loads the weekly report. The model's tokenizer prepares the text for AI processing, and the model then generates a concise summary of the key security trends.
Output: An AI-generated summary draft report, saved as a CSV file for review and further analysis.
