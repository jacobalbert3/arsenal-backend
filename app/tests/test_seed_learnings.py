# test_seed_learnings.py
# ✅ Script to insert a user and 50 learnings into Railway Postgres DB with OpenAI embeddings

import os
import psycopg2
from psycopg2.extras import execute_values
from openai import OpenAI
import numpy as np
from passlib.hash import bcrypt
from dotenv import load_dotenv
from urllib.parse import urlparse
import time
import getpass

load_dotenv()

# Configuration
EMAIL = "test@test.com"
PASSWORD = "123456"
VECTOR_DIM = 1536  # OpenAI ada-002 dimension

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_embedding(text):
    # Add retry logic for API rate limits
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(2 ** attempt)  # Exponential backoff

# Get database configuration based on environment
def get_db_config():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        database_url = f"postgresql://{getpass.getuser()}@localhost/arsenal_db"
  
    
    url = urlparse(database_url)
    return {
        "dbname": url.path[1:],  # Remove leading slash
        "user": url.username,
        "password": url.password,
        "host": url.hostname,
        "port": url.port # Required for Railway
    }

# Your existing learnings list remains the same
learnings = [
    ("Used useEffect to fetch user profile on mount", "useEffect(() => { axios.get('/api/profile').then(res => setUser(res.data)); }, []);", "useEffect", "axios", "/pages/profile.tsx"),
    ("Built REST API with FastAPI for task management", "@app.post('/tasks')\ndef create_task(task: Task):\n    db.save(task)", "create_task", "fastapi", "/api/tasks.py"),
    ("Configured CORS in FastAPI", "app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])", "cors_setup", "fastapi", "/main.py"),
    ("Built authentication service using Firebase SDK", "firebase.auth().createUserWithEmailAndPassword(email, password)", "createUser", "firebase", "/services/auth.ts"),
    ("Created responsive navbar using Tailwind", "<nav className=\"flex justify-between px-4 py-2 bg-black text-white\">...</nav>", "Navbar", "tailwindcss", "/components/Navbar.tsx"),
    ("Optimized component re-renders using React.memo", "const MemoizedList = React.memo(MyListComponent)", "MemoizedList", "react", "/components/List.tsx"),
    ("Cached expensive computation with useMemo", "const value = useMemo(() => computeHeavy(input), [input])", "useMemoExample", "react", "/hooks/useHeavy.ts"),
    ("Built dark mode toggle using localStorage and useEffect", "useEffect(() => { const theme = localStorage.getItem('theme'); setDark(theme === 'dark'); }, [])", "useTheme", "react", "/hooks/useTheme.ts"),
    ("Logged structured errors using Sentry", "Sentry.captureException(error)", "logError", "sentry", "/utils/log.ts"),
    ("Deployed Node.js app to Heroku with Procfile", "web: node index.js", "Procfile", "heroku", "/Procfile"),
    ("Created table relationships in Prisma schema", "model Post { id Int @id @default(autoincrement()) author User @relation(fields: [authorId], references: [id]) authorId Int }", "PostModel", "prisma", "/prisma/schema.prisma"),
    ("Built markdown editor with preview panel", "<ReactMarkdown>{markdown}</ReactMarkdown>", "MarkdownEditor", "react-markdown", "/components/Editor.tsx"),
    ("Implemented pagination in MongoDB with skip & limit", "db.collection('items').find().skip(10).limit(10)", "paginateItems", "mongodb", "/db/query.js"),
    ("Uploaded files using S3 pre-signed URLs", "s3.getSignedUrl('putObject', { Bucket: ..., Key: ... })", "uploadToS3", "aws-sdk", "/utils/s3.ts"),
    ("Used zod for input validation in tRPC procedure", "const schema = z.object({ email: z.string().email() })", "validateInput", "zod", "/server/schema.ts"),
    ("Built protected Next.js API route with session check", "if (!session) return res.status(401).end()", "checkSession", "next-auth", "/pages/api/protected.ts"),
    ("Extracted constants into config file for reuse", "export const BASE_URL = process.env.API_URL", "config", "env", "/config/constants.ts"),
    ("Connected frontend form to backend using fetch", "await fetch('/api/data', { method: 'POST', body: JSON.stringify(payload) })", "submitForm", "fetch", "/utils/api.ts"),
    ("Built drag-and-drop file uploader with react-dropzone", "<Dropzone onDrop={handleDrop}>...</Dropzone>", "FileDrop", "react-dropzone", "/components/FileDrop.tsx"),
    ("Created custom toast notification hook", "const { showToast } = useToast()", "useToast", "custom", "/hooks/useToast.ts"),
    ("Used Immer to handle immutable state updates", "const nextState = produce(state, draft => { draft.count++ })", "useImmer", "immer", "/reducers/counter.ts"),
    ("Styled modal with backdrop blur using Tailwind", "<div className=\"fixed inset-0 backdrop-blur-sm bg-black/30\">...</div>", "Modal", "tailwindcss", "/components/Modal.tsx"),
    ("Queried related documents with Mongoose populate", "Post.find().populate('author')", "populatePosts", "mongoose", "/models/post.js"),
    ("Used useReducer for complex form state", "const [state, dispatch] = useReducer(reducer, initialState)", "useFormReducer", "react", "/hooks/useFormReducer.ts"),
    ("Integrated Stripe checkout session", "const session = await stripe.checkout.sessions.create({ ... })", "createCheckout", "stripe", "/server/stripe.ts"),
    ("Rendered code blocks with syntax highlighting", "<SyntaxHighlighter language=\"js\">{code}</SyntaxHighlighter>", "CodeBlock", "react-syntax-highlighter", "/components/CodeBlock.tsx"),
    ("Wrote integration test using Supertest", "await request(app).post('/login').send({ email, password })", "testLogin", "supertest", "/tests/auth.test.ts"),
    ("Mapped over nested API data to display UI", "data.sections.map(section => section.items.map(...))", "renderNestedItems", "react", "/components/NestedList.tsx"),
    ("Created CLI with argparse in Python", "parser = argparse.ArgumentParser(); parser.add_argument('--env')", "cliInit", "argparse", "/scripts/cli.py"),
    ("Deployed static site with GitHub Pages", "npm run build && npx gh-pages -d dist", "deploySite", "gh-pages", "/scripts/deploy.js"),
    ("Connected Docker container to Postgres DB", "DB_HOST=host.docker.internal", "dockerConfig", "docker", "/docker-compose.yml"),
    ("Used ternary expression in JSX", "{isLoggedIn ? <Dashboard /> : <Login />}", "ConditionalUI", "react", "/components/AuthGate.tsx"),
    ("Built dropdown using headless UI", "<Listbox value={selected} onChange={setSelected}>...</Listbox>", "CustomDropdown", "headlessuit", "/components/Dropdown.tsx"),
    ("Set up lazy loading with React.lazy", "const LazyPage = React.lazy(() => import('./Page'))", "LazyPage", "react", "/pages/LazyPage.tsx"),
    ("Used SWR for stale-while-revalidate data fetch", "const { data } = useSWR('/api/user', fetcher)", "useUser", "swr", "/hooks/useUser.ts"),
    ("Added scroll animations with Framer Motion", "<motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} />", "AnimatedSection", "framer-motion", "/components/Section.tsx"),
    ("Prevented SSR error with window check", "if (typeof window !== 'undefined') { ... }", "useClient", "nextjs", "/hooks/useClient.ts"),
    ("Simulated API response with MSW", "rest.get('/user', (req, res, ctx) => res(ctx.json(mockUser)))", "mockUserApi", "msw", "/mocks/handlers.js"),
    ("Enforced rate limit in Express API", "app.use(rateLimit({ windowMs: 60_000, max: 100 }))", "rateLimit", "express-rate-limit", "/server/index.js"),
    ("Built analytics tracker using localStorage and fetch", "localStorage.setItem('visited', true); fetch('/track', { method: 'POST' })", "trackVisit", "analytics", "/utils/tracker.js"),
    ("Wrote bash script to clean logs", "#!/bin/bash\nrm -rf /var/logs/*.log", "cleanLogs", "bash", "/scripts/clean.sh"),
    ("Wrote SQL query to find top 5 customers", "SELECT name FROM customers ORDER BY spend DESC LIMIT 5", "topCustomers", "sql", "/queries/top_customers.sql"),
    ("Used reduce to aggregate cart total", "cart.reduce((sum, item) => sum + item.price * item.qty, 0)", "calcTotal", "js", "/utils/calc.ts"),
    ("Wrote GraphQL mutation for comment submission", "mutation AddComment($postId: ID!, $content: String!) { addComment(postId: $postId, content: $content) { id } }", "addCommentMutation", "graphql", "/graphql/mutations.ts"),
    ("Created email templates using MJML", "<mj-section><mj-text>Welcome!</mj-text></mj-section>", "welcomeEmail", "mjml", "/emails/welcome.mjml"),
    ("Used lodash debounce to limit API calls", "const handler = debounce(search, 300)", "debouncedSearch", "lodash", "/utils/debounce.ts"),
    ("Built Dockerfile for React app", "FROM node:18\nWORKDIR /app\nCOPY . .\nRUN npm install\nCMD [\"npm\", \"start\"]", "dockerReact", "docker", "/Dockerfile"),
    ("Created QR code with qrcode.react", "<QRCode value={url} />", "QRCodeGen", "qrcode.react", "/components/QRCode.tsx"),
    ("Implemented infinite scroll with IntersectionObserver", "useEffect(() => { const observer = new IntersectionObserver(...) })", "useInfiniteScroll", "react", "/hooks/useInfiniteScroll.ts")
]

def main():
    try:
        # Get DB configuration
        DB_CONFIG = get_db_config()
        
        # Connect to Railway Postgres
        print("Connecting to Railway Postgres...")
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print("Cleaning up existing test data...")
        # Remove in correct order due to foreign key constraints
        cur.execute("DELETE FROM api_keys WHERE user_id IN (SELECT id FROM users WHERE email = %s)", (EMAIL,))
        cur.execute("DELETE FROM learnings WHERE user_id IN (SELECT id FROM users WHERE email = %s)", (EMAIL,))
        cur.execute("DELETE FROM projects WHERE user_id IN (SELECT id FROM users WHERE email = %s)", (EMAIL,))
        cur.execute("DELETE FROM users WHERE email = %s", (EMAIL,))
        conn.commit()
        
        print("Creating test user...")
        # Create test user
        cur.execute(
            "INSERT INTO users (email, password) VALUES (%s, %s) RETURNING id",
            (EMAIL, bcrypt.hash(PASSWORD))
        )
        user_id = cur.fetchone()[0]
        
        print("Creating test project...")
        # Create test project
        cur.execute(
            "INSERT INTO projects (user_id, name) VALUES (%s, %s) RETURNING id",
            (user_id, "Test Project")
        )
        project_id = cur.fetchone()[0]
        
        print("Generating embeddings and inserting learnings...")
        # Embed and insert learnings
        entries = []
        for i, (desc, code, func, lib, path) in enumerate(learnings, 1):
            print(f"Processing learning {i}/{len(learnings)}...")
            vec = get_embedding(desc)
            entries.append((project_id, path, func, lib, desc, code, user_id, vec))
            
            # Batch process in groups of 10 to avoid rate limits
            if i % 10 == 0:
                time.sleep(2)
        
        execute_values(cur, """
            INSERT INTO learnings (project_id, file_path, function_name, library_name, description, code_snippet, user_id, embedding)
            VALUES %s
        """, entries)
        
        conn.commit()
        print("✅ Test user and learnings inserted successfully into Railway Postgres!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()
