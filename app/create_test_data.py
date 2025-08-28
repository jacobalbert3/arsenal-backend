# Used to create test data for development/testing
import os
import asyncio
from sqlalchemy import create_engine, text
from app.models import metadata
from app.models.project import projects
from app.models.learnings import learnings
from app.models.users import users
from app.db import database
from passlib.hash import bcrypt
from dotenv import load_dotenv
import getpass
import numpy as np

# Load env stuff
load_dotenv()

# Test data for learnings
TEST_LEARNINGS = [
    # React/JavaScript
    {"library": "React", "function": "useState", "description": "React hook for managing state in functional components", "code": "const [count, setCount] = useState(0);", "file": "src/components/Counter.jsx"},
    {"library": "React", "function": "useEffect", "description": "React hook for handling side effects in components", "code": "useEffect(() => { console.log('Component mounted'); }, []);", "file": "src/components/DataFetcher.jsx"},
    {"library": "React", "function": "useContext", "description": "React hook for consuming context values", "code": "const theme = useContext(ThemeContext);", "file": "src/context/ThemeProvider.jsx"},
    {"library": "React Router", "function": "useNavigate", "description": "Hook for programmatic navigation in React Router", "code": "const navigate = useNavigate(); navigate('/dashboard');", "file": "src/components/Navigation.jsx"},
    {"library": "React Router", "function": "useParams", "description": "Hook to access URL parameters in React Router", "code": "const { id } = useParams();", "file": "src/components/UserProfile.jsx"},
    
    # Node.js/Express
    {"library": "Express", "function": "app.get", "description": "Express route handler for GET requests", "code": "app.get('/api/users', (req, res) => { res.json(users); });", "file": "src/routes/users.js"},
    {"library": "Express", "function": "app.post", "description": "Express route handler for POST requests", "code": "app.post('/api/users', (req, res) => { const user = req.body; users.push(user); res.status(201).json(user); });", "file": "src/routes/users.js"},
    {"library": "Express", "function": "middleware", "description": "Express middleware for request processing", "code": "app.use(express.json()); app.use(cors());", "file": "src/app.js"},
    {"library": "Node.js", "function": "fs.readFile", "description": "Node.js file system read operation", "code": "fs.readFile('data.json', 'utf8', (err, data) => { if (err) throw err; console.log(data); });", "file": "src/utils/fileHandler.js"},
    {"library": "Node.js", "function": "fs.writeFile", "description": "Node.js file system write operation", "code": "fs.writeFile('output.json', JSON.stringify(data), (err) => { if (err) throw err; });", "file": "src/utils/fileHandler.js"},
    
    # Python
    {"library": "FastAPI", "function": "app.get", "description": "FastAPI route decorator for GET endpoints", "code": "@app.get('/users') async def get_users(): return users", "file": "src/routes/users.py"},
    {"library": "FastAPI", "function": "app.post", "description": "FastAPI route decorator for POST endpoints", "code": "@app.post('/users') async def create_user(user: User): return user", "file": "src/routes/users.py"},
    {"library": "FastAPI", "function": "Depends", "description": "FastAPI dependency injection", "code": "async def get_db(): return database", "file": "src/dependencies.py"},
    {"library": "SQLAlchemy", "function": "session.query", "description": "SQLAlchemy ORM query operation", "code": "users = session.query(User).all()", "file": "src/models/user.py"},
    {"library": "SQLAlchemy", "function": "session.add", "description": "SQLAlchemy ORM add operation", "code": "session.add(new_user); session.commit()", "file": "src/models/user.py"},
    {"library": "Pandas", "function": "pd.read_csv", "description": "Pandas CSV file reading", "code": "df = pd.read_csv('data.csv')", "file": "src/data/loader.py"},
    {"library": "Pandas", "function": "df.groupby", "description": "Pandas groupby operation", "code": "grouped = df.groupby('category').sum()", "file": "src/data/analysis.py"},
    {"library": "NumPy", "function": "np.array", "description": "NumPy array creation", "code": "arr = np.array([1, 2, 3, 4, 5])", "file": "src/utils/math.py"},
    {"library": "NumPy", "function": "np.mean", "description": "NumPy mean calculation", "code": "mean = np.mean(data)", "file": "src/utils/math.py"},
    
    # Database
    {"library": "PostgreSQL", "function": "SELECT", "description": "PostgreSQL SELECT query", "code": "SELECT * FROM users WHERE active = true;", "file": "src/db/queries.sql"},
    {"library": "PostgreSQL", "function": "INSERT", "description": "PostgreSQL INSERT statement", "code": "INSERT INTO users (name, email) VALUES ($1, $2);", "file": "src/db/queries.sql"},
    {"library": "MongoDB", "function": "find", "description": "MongoDB find operation", "code": "db.users.find({active: true})", "file": "src/db/mongo.js"},
    {"library": "MongoDB", "function": "insertOne", "description": "MongoDB insert operation", "code": "db.users.insertOne({name: 'John', email: 'john@example.com'})", "file": "src/db/mongo.js"},
    {"library": "Redis", "function": "SET", "description": "Redis SET command", "code": "SET user:123 'John Doe'", "file": "src/cache/redis.js"},
    {"library": "Redis", "function": "GET", "description": "Redis GET command", "code": "GET user:123", "file": "src/cache/redis.js"},
    
    # Testing
    {"library": "Jest", "function": "describe", "description": "Jest test suite definition", "code": "describe('User API', () => { test('should create user', () => {}); });", "file": "tests/user.test.js"},
    {"library": "Jest", "function": "test", "description": "Jest individual test case", "code": "test('should return user by id', () => { expect(getUser(1)).toBeDefined(); });", "file": "tests/user.test.js"},
    {"library": "Pytest", "function": "def test", "description": "Pytest test function", "code": "def test_create_user(): assert create_user('John') is not None", "file": "tests/test_users.py"},
    {"library": "Pytest", "function": "pytest.fixture", "description": "Pytest fixture definition", "code": "@pytest.fixture def db(): return Database()", "file": "tests/conftest.py"},
    
    # CSS/UI
    {"library": "Tailwind CSS", "function": "flex", "description": "Tailwind CSS flexbox utility", "code": "<div className='flex items-center justify-center'>", "file": "src/components/Layout.jsx"},
    {"library": "Tailwind CSS", "function": "grid", "description": "Tailwind CSS grid utility", "code": "<div className='grid grid-cols-3 gap-4'>", "file": "src/components/Grid.jsx"},
    {"library": "CSS", "function": "flexbox", "description": "CSS flexbox layout", "code": "display: flex; justify-content: center; align-items: center;", "file": "src/styles/layout.css"},
    {"library": "CSS", "function": "grid", "description": "CSS grid layout", "code": "display: grid; grid-template-columns: repeat(3, 1fr);", "file": "src/styles/layout.css"},
    
    # Authentication
    {"library": "JWT", "function": "jwt.sign", "description": "JWT token signing", "code": "const token = jwt.sign(payload, secret, {expiresIn: '1h'});", "file": "src/auth/jwt.js"},
    {"library": "JWT", "function": "jwt.verify", "description": "JWT token verification", "code": "const decoded = jwt.verify(token, secret);", "file": "src/auth/jwt.js"},
    {"library": "bcrypt", "function": "hash", "description": "Password hashing with bcrypt", "code": "const hashedPassword = await bcrypt.hash(password, 10);", "file": "src/auth/password.js"},
    {"library": "bcrypt", "function": "compare", "description": "Password comparison with bcrypt", "code": "const isValid = await bcrypt.compare(password, hashedPassword);", "file": "src/auth/password.js"},
    
    # API/HTTP
    {"library": "Axios", "function": "get", "description": "Axios HTTP GET request", "code": "const response = await axios.get('/api/users');", "file": "src/api/client.js"},
    {"library": "Axios", "function": "post", "description": "Axios HTTP POST request", "code": "const response = await axios.post('/api/users', userData);", "file": "src/api/client.js"},
    {"library": "Fetch API", "function": "fetch", "description": "JavaScript Fetch API", "code": "const response = await fetch('/api/users'); const data = await response.json();", "file": "src/api/client.js"},
    
    # State Management
    {"library": "Redux", "function": "createSlice", "description": "Redux Toolkit slice creation", "code": "const userSlice = createSlice({name: 'user', initialState, reducers: {}});", "file": "src/store/userSlice.js"},
    {"library": "Redux", "function": "useSelector", "description": "Redux hook for selecting state", "code": "const user = useSelector(state => state.user);", "file": "src/components/UserProfile.jsx"},
    {"library": "Zustand", "function": "create", "description": "Zustand store creation", "code": "const useStore = create((set) => ({count: 0, increment: () => set(state => ({count: state.count + 1}))}));", "file": "src/store/store.js"},
    
    # File Handling
    {"library": "Multer", "function": "upload", "description": "Multer file upload middleware", "code": "const upload = multer({dest: 'uploads/'}); app.post('/upload', upload.single('file'));", "file": "src/routes/upload.js"},
    {"library": "Sharp", "function": "resize", "description": "Sharp image resizing", "code": "await sharp('input.jpg').resize(300, 200).toFile('output.jpg');", "file": "src/utils/image.js"},
    
    # Validation
    {"library": "Joi", "function": "validate", "description": "Joi schema validation", "code": "const {error, value} = Joi.validate(data, schema);", "file": "src/validation/user.js"},
    {"library": "Pydantic", "function": "BaseModel", "description": "Pydantic model definition", "code": "class User(BaseModel): name: str; email: str", "file": "src/models/user.py"},
    
    # Error Handling
    {"library": "Express", "function": "error handler", "description": "Express error handling middleware", "code": "app.use((err, req, res, next) => { res.status(500).json({error: err.message}); });", "file": "src/middleware/error.js"},
    {"library": "Python", "function": "try-except", "description": "Python exception handling", "code": "try: result = risky_operation() except Exception as e: logger.error(e)", "file": "src/utils/error_handler.py"},
    
    # Logging
    {"library": "Winston", "function": "logger", "description": "Winston logging setup", "code": "const logger = winston.createLogger({level: 'info', format: winston.format.json()});", "file": "src/utils/logger.js"},
    {"library": "Python", "function": "logging", "description": "Python logging configuration", "code": "logging.basicConfig(level=logging.INFO); logger = logging.getLogger(__name__)", "file": "src/utils/logger.py"},
    
    # Performance
    {"library": "React", "function": "React.memo", "description": "React memo for performance optimization", "code": "const MemoizedComponent = React.memo(MyComponent);", "file": "src/components/OptimizedComponent.jsx"},
    {"library": "React", "function": "useMemo", "description": "React useMemo for expensive calculations", "code": "const expensiveValue = useMemo(() => computeExpensiveValue(a, b), [a, b]);", "file": "src/components/ExpensiveComponent.jsx"},
    
    # Security
    {"library": "Helmet", "function": "helmet", "description": "Express security middleware", "code": "app.use(helmet());", "file": "src/app.js"},
    {"library": "CORS", "function": "cors", "description": "CORS middleware for cross-origin requests", "code": "app.use(cors({origin: 'http://localhost:3000'}));", "file": "src/app.js"},
    
    # Data Processing
    {"library": "Lodash", "function": "map", "description": "Lodash array mapping", "code": "const names = _.map(users, 'name');", "file": "src/utils/data.js"},
    {"library": "Lodash", "function": "filter", "description": "Lodash array filtering", "code": "const activeUsers = _.filter(users, {active: true});", "file": "src/utils/data.js"},
    
    # Date/Time
    {"library": "Moment.js", "function": "moment", "description": "Moment.js date manipulation", "code": "const now = moment(); const formatted = moment().format('YYYY-MM-DD');", "file": "src/utils/date.js"},
    {"library": "Python", "function": "datetime", "description": "Python datetime handling", "code": "from datetime import datetime; now = datetime.now()", "file": "src/utils/date.py"},
    
    # Configuration
    {"library": "dotenv", "function": "config", "description": "Environment variable loading", "code": "require('dotenv').config();", "file": "src/config/env.js"},
    {"library": "Python", "function": "os.environ", "description": "Python environment variables", "code": "import os; api_key = os.environ.get('API_KEY')", "file": "src/config/env.py"},
    
    # Async/Await
    {"library": "JavaScript", "function": "async/await", "description": "JavaScript async/await pattern", "code": "async function fetchData() { const response = await fetch('/api/data'); return response.json(); }", "file": "src/utils/async.js"},
    {"library": "Python", "function": "async/await", "description": "Python async/await pattern", "code": "async def fetch_data(): async with aiohttp.ClientSession() as session: async with session.get('/api/data') as response: return await response.json()", "file": "src/utils/async.py"},
    
    # TypeScript
    {"library": "TypeScript", "function": "interface", "description": "TypeScript interface definition", "code": "interface User { id: number; name: string; email: string; }", "file": "src/types/user.ts"},
    {"library": "TypeScript", "function": "type", "description": "TypeScript type definition", "code": "type Status = 'pending' | 'success' | 'error';", "file": "src/types/common.ts"},
    
    # Build Tools
    {"library": "Webpack", "function": "entry", "description": "Webpack entry point configuration", "code": "module.exports = { entry: './src/index.js', output: { path: path.resolve(__dirname, 'dist') } };", "file": "webpack.config.js"},
    {"library": "Vite", "function": "defineConfig", "description": "Vite configuration", "code": "export default defineConfig({ plugins: [react()], server: { port: 3000 } });", "file": "vite.config.js"},
    
    # Database ORM
    {"library": "Prisma", "function": "prisma.client", "description": "Prisma client usage", "code": "const user = await prisma.user.findUnique({ where: { id: 1 } });", "file": "src/db/client.js"},
    {"library": "Prisma", "function": "prisma.schema", "description": "Prisma schema definition", "code": "model User { id Int @id @default(autoincrement()); name String; email String @unique; }", "file": "prisma/schema.prisma"},
    
    # GraphQL
    {"library": "Apollo", "function": "useQuery", "description": "Apollo GraphQL query hook", "code": "const { data, loading, error } = useQuery(GET_USERS);", "file": "src/components/UserList.jsx"},
    {"library": "Apollo", "function": "useMutation", "description": "Apollo GraphQL mutation hook", "code": "const [createUser, { data }] = useMutation(CREATE_USER);", "file": "src/components/CreateUser.jsx"},
    
    # WebSocket
    {"library": "Socket.io", "function": "emit", "description": "Socket.io event emission", "code": "io.emit('message', { text: 'Hello world' });", "file": "src/socket/server.js"},
    {"library": "Socket.io", "function": "on", "description": "Socket.io event listening", "code": "socket.on('message', (data) => { console.log(data); });", "file": "src/socket/client.js"},
    
    # Machine Learning
    {"library": "TensorFlow", "function": "tf.sequential", "description": "TensorFlow sequential model", "code": "const model = tf.sequential({ layers: [tf.layers.dense({units: 1, inputShape: [1]})] });", "file": "src/ml/model.js"},
    {"library": "Scikit-learn", "function": "LinearRegression", "description": "Scikit-learn linear regression", "code": "from sklearn.linear_model import LinearRegression; model = LinearRegression(); model.fit(X, y);", "file": "src/ml/regression.py"},
    
    # DevOps
    {"library": "Docker", "function": "Dockerfile", "description": "Docker container definition", "code": "FROM node:16; WORKDIR /app; COPY package*.json ./; RUN npm install;", "file": "Dockerfile"},
    {"library": "Git", "function": "git commit", "description": "Git commit command", "code": "git add .; git commit -m 'Add new feature';", "file": "scripts/deploy.sh"},
]

async def create_test_data():
    # Database connection setup
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        DATABASE_URL = f"postgresql://{getpass.getuser()}@localhost/arsenal_db"
    else:
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://')

    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        connect_args={"connect_timeout": 30}
    )

    try:
        # Test database connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("Database connection successful.")

        # Create test user
        test_user_email = "test@example.com"
        test_user_password = "testpassword123"
        hashed_password = bcrypt.hash(test_user_password)
        
        # Check if test user already exists
        existing_user = await database.fetch_one(
            users.select().where(users.c.email == test_user_email)
        )
        
        if existing_user:
            user_id = existing_user['id']
            print(f"Test user already exists with ID: {user_id}")
        else:
            # Insert test user
            user_query = users.insert().values(
                email=test_user_email,
                password=hashed_password
            )
            user_id = await database.execute(user_query)
            print(f"Created test user with ID: {user_id}")

        # Create test project
        test_project_name = "Test Development Project"
        
        # Check if test project already exists
        existing_project = await database.fetch_one(
            projects.select().where(
                projects.c.user_id == user_id,
                projects.c.name == test_project_name
            )
        )
        
        if existing_project:
            project_id = existing_project['id']
            print(f"Test project already exists with ID: {project_id}")
        else:
            # Insert test project
            project_query = projects.insert().values(
                name=test_project_name,
                github_repo="https://github.com/testuser/test-project",
                user_id=user_id
            )
            project_id = await database.execute(project_query)
            print(f"Created test project with ID: {project_id}")

        # Insert test learnings
        learning_count = 0
        for learning in TEST_LEARNINGS:
            # Check if learning already exists
            existing_learning = await database.fetch_one(
                learnings.select().where(
                    learnings.c.user_id == user_id,
                    learnings.c.project_id == project_id,
                    learnings.c.function_name == learning['function'],
                    learnings.c.library_name == learning['library']
                )
            )
            
            if not existing_learning:
                # Generate a random embedding (1536 dimensions for OpenAI embeddings)
                embedding = np.random.rand(1536).tolist()
                
                learning_query = learnings.insert().values(
                    project_id=project_id,
                    file_path=learning['file'],
                    function_name=learning['function'],
                    library_name=learning['library'],
                    description=learning['description'],
                    code_snippet=learning['code'],
                    user_id=user_id,
                    embedding=embedding
                )
                await database.execute(learning_query)
                learning_count += 1

        print(f"Created {learning_count} new test learnings")
        print(f"Total learnings in database: {len(TEST_LEARNINGS)}")
        
        print("\nTest data creation complete!")
        print(f"Test user email: {test_user_email}")
        print(f"Test user password: {test_user_password}")
        print(f"User ID: {user_id}")
        print(f"Project ID: {project_id}")
        
    except Exception as e:
        print(f"Error creating test data: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(create_test_data())
