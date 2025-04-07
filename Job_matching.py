# import pandas as pd
# from keywords import extract_all_keywords


# resume_keywords = extract_all_keywords("gowtham1.pdf")
# print("Resume Keywords:", resume_keywords)
import pandas as pd
import re

resume_keywords = skills_list = [
    "Python", "Java", "Solidity", "Shell Scripting", "HTML", "CSS", "JavaScript", "TypeScript", "SQL",
    "Node.js", "Flask", "Django", "FastAPI", "Spring Boot", "Express.js", "GraphQL", "RestAPIs", "Web3.js", "Kafka", "jQuery", "SOAP", "ReactJS", "NextJS", "Figma", "Linux/Unix", "JSON", "Software Development Life Cycle", "MVC", "JUnit", "Android", "Swift", "LLM’s", "OpenAI API",
    "Unit Testing", "Integration Testing", "Load Testing", "Git", "GitHub", "Postman", "Heroku",
    "MySQL", "PostgreSQL", "MS SQL", "DynamoDB", "NoSQL", "Oracle", "AWS RDS MongoDB", "PL/SQL", "Redis",
    "RStudio", "Pandas", "NumPy", "Matplotlib", "PyTorch", "Jupyter", "Tableau", "PowerBI",
    "Data Structures & Algorithms", "Scalability", "Performance Tuning", "Debugging", "System Design", "Code Health",
    "AWSS3", "AWSIAM", "AWSEKS", "AWSEC2", "AWSSNS", "AWSSQS", "AWSELB", "AWSCloudWatch", "VPC", "AWS Lambda", "AWSCognito", "AWSRoute53", "AWSGlue", "AzureAKS", "AzureApp Services", "Azure Blob Storage", "GCPCompute Engine", "GCPCloud Run", "GCPBigQuery", "Docker", "Kubernetes", "Terraform", "Ansible", "Jenkins", "CI/CD Pipelines", "Grafana", "ELK Stack", "Datadog", "Prometheus", "Grafana", "ELK Stack", "AWS CloudWatch", "Git", "GitHub Actions",
    "GitLab", "ArgoCD", "Helm", "kubelet", "Puppet"
]


simple_stopwords = {
    "the", "and", "for", "with", "that", "this", "are", "was", "were", "is", "in", "on", "a", "an", "of", "to", "it", "by", "as", "at", "or", "if"
}

def extract_job_description_keywords(text):
    """
    Extract candidate keywords from the job description text by tokenizing, 
    lowercasing, and filtering out common stopwords and short words.
    (This is an optional step if you want to analyze the description separately.)
    """
    # Find all word tokens
    words = re.findall(r'\b\w+\b', text.lower())
    # Filter out stopwords and words shorter than 3 characters
    candidate_keywords = {word for word in words if word not in simple_stopwords and len(word) > 2}
    return candidate_keywords

def compute_matched_keywords(text, resume_keywords):
    """
    Return a list of resume keywords that are found as substrings in the given text (case-insensitive).
    This approach preserves multi-word phrases.
    """
    matched = []
    text_lower = text.lower()
    for kw in resume_keywords:
        if kw.lower() in text_lower:
            matched.append(kw)
    return matched

def compute_keyword_score(matched, total_keywords):
    """
    Compute the keyword match score as a percentage based on the fraction of resume keywords found.
    """
    if total_keywords:
        return (len(matched) / total_keywords) * 100
    return 0

def rank_jobs(job_csv, resume_keywords):
    """
    Load job data from a CSV file, compute the matched keywords and match score for each job 
    based on its combined text (title, job role, description), and return a DataFrame of ranked jobs.
    Also appends the matched keywords as a comma-separated string.
    """
    df = pd.read_csv(job_csv)
    # Create a combined text field for each job
    df['combined_text'] = (
        df['title'].fillna('') + " " +
        df.get('job_role', '') + " " +
        df.get('description', '')
    )
    # For each job, get the list of matched resume keywords
    df['matched_keywords'] = df['combined_text'].apply(lambda x: compute_matched_keywords(x, resume_keywords))
    # Convert the list to a comma-separated string for CSV output
    df['matched_keywords_str'] = df['matched_keywords'].apply(lambda kws: ", ".join(kws))
    # Compute the match score (percentage of resume keywords found)
    df['match_score'] = df['matched_keywords'].apply(lambda kws: compute_keyword_score(kws, len(resume_keywords)))
    df['match_score'] = df['match_score'].round(2)
    
    # Sort jobs by match score (highest first)
    df_sorted = df.sort_values(by='match_score', ascending=False)
    return df_sorted

if __name__ == "__main__":
    job_csv = "linkedin_jobs.csv"
    
    print("Using resume keywords:")
    print(resume_keywords)
    
    # Rank the jobs using the computed match score based solely on keyword matching.
    ranked_jobs = rank_jobs(job_csv, resume_keywords)
    
    # Print all jobs with their computed match score and matched keywords
    print("Jobs with computed match score (in percentage) and matched keywords:")
    print(ranked_jobs[['title', 'job_role', 'match_score', 'matched_keywords_str']])
    
    # Save the ranked jobs (with matched keywords) to a new CSV file.
    ranked_jobs.to_csv("ranked_jobs_with_keywords.csv", index=False)
    print("Ranked jobs with matched keywords exported to ranked_jobs_with_keywords.csv")