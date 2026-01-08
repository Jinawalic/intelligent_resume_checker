import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import PyPDF2

# --- NLTK DATA INITIALIZATION ---
# We download these every time the script runs to ensure the environment is ready.
nltk.download('stopwords', quiet=True)
nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)  # <--- THE CRITICAL FIX

stop_words = set(stopwords.words('english'))

def clean_text(text):
    """Cleans text by removing URLs, punctuation, and stopwords."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'http\S+\s*', ' ', text)  # remove URLs
    text = re.sub(r'[^\w\s]', ' ', text)      # remove punctuation
    words = word_tokenize(text)
    filtered = [w for w in words if w not in stop_words and not w.isdigit()]
    return " ".join(filtered)

def extract_text_from_pdf(file_path):
    """Extracts raw text from a PDF file."""
    text = ""
    try:
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                content = page.extract_text()
                if content:
                    text += content
    except Exception as e:
        print(f"Error reading PDF {file_path}: {e}")
    return text

def get_similarity_score(job_desc, resume_text):
    """Calculates Cosine Similarity score using TF-IDF."""
    # Convert text to numerical vectors
    documents = [job_desc, resume_text]
    vectorizer = TfidfVectorizer()
    
    try:
        tfidf_matrix = vectorizer.fit_transform(documents)
        # Cosine Similarity Formula: (A . B) / (||A|| * ||B||)
        score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
        return round(score[0][0] * 100, 2)
    except Exception:
        # Returns 0 if vectors cannot be compared (e.g., empty text)
        return 0.0