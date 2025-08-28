# Cluely Agents

A collection of AI agents built for various use cases using the Cluely platform.

## Agents

### 🤖 cluely-ben-agent
A sales and customer service agent designed to handle customer inquiries and sales interactions.

**Location:** `cluely-ben-agent/`

**Features:**
- Customer inquiry handling
- Sales conversation management
- Intelligent response generation

**Setup:**
```bash
cd cluely-ben-agent
pip install -r requirements.txt
python main.py
```

## Adding New Agents

To add a new agent to this repository:

1. Create a new directory in the root: `new-agent-name/`
2. Include the following files:
   - `main.py` - Main agent entry point
   - `requirements.txt` - Python dependencies
   - `README.md` - Agent-specific documentation
   - `pyproject.toml` - Project configuration

## Development

### Prerequisites
- Python 3.8+
- Virtual environment (recommended)

### Setup
1. Clone the repository
2. Navigate to the specific agent directory
3. Create a virtual environment: `python -m venv venv`
4. Activate the virtual environment: `source venv/bin/activate` (Unix) or `venv\Scripts\activate` (Windows)
5. Install dependencies: `pip install -r requirements.txt`

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-agent`
3. Commit your changes: `git commit -am 'Add new agent'`
4. Push to the branch: `git push origin feature/new-agent`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
