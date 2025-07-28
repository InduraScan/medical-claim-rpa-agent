# 🏥 Medical Claim RPA AI Agent

An intelligent automation system for processing medical claims with AI-powered decision making and Google Drive integration.

## 🎯 Features

- **AI-Powered Claim Splitting**: Automatically splits medical claims exceeding 28 lines while maintaining clinical relationships
- **Google Drive Integration**: Seamless file pickup and delivery from Google Drive
- **Medical Code Intelligence**: Built-in knowledge of ICD, HCPCS, and revenue codes
- **Business Rule Engine**: Implements complex healthcare billing rules
- **Executive Dashboard**: Clean UI for leadership demos with processing analytics
- **Audit Trail**: Complete AI reasoning and decision documentation

## 🚀 Quick Start

### 1. Local Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/medical-claim-rpa-agent.git
cd medical-claim-rpa-agent

# Install dependencies
pip install -r requirements.txt

# Run setup script
python setup.py

# Start the application
streamlit run app.py
```

### 2. Production Deployment (Render)

1. Fork this repository
2. Create a Render account
3. Connect your GitHub repository
4. Set environment variables (see deployment guide)
5. Deploy!

## 📋 Business Rules Implemented

### Core Processing Rules
- **28-Line Limit**: Automatically splits claims exceeding 28 line items
- **ER Consolidation**: Merges ER visits within 24-hour windows
- **Imaging Grouping**: Associates imaging services with related ER visits
- **Service Prioritization**: Orders services by clinical importance

### Medical Code Recognition
- Emergency Room codes (99281-99285, 0450-0459)
- Diagnostic imaging (CT, MRI, Ultrasound)
- Laboratory services (CBC, CMP, specialized tests)
- Surgical procedures and ICU services
- Medications and infusions

## 🏗️ Architecture

```
📁 medical-claim-rpa-agent/
├── 🎯 app.py                 # Main Streamlit application
├── 🔧 claim_processor.py     # Core claim processing logic
├── ☁️ google_drive_handler.py # Google Drive API integration
├── 🧠 ai_reasoner.py         # AI decision reasoning engine
├── ⚙️ config.py              # Configuration management
├── 🛠️ setup.py              # Interactive setup script
├── 📦 requirements.txt       # Python dependencies
├── 🐳 Dockerfile            # Container configuration
├── 🌐 render.yaml           # Render deployment config
└── 📖 DEPLOYMENT_GUIDE.md   # Step-by-step deployment
```

## 🎮 Usage

### Processing Claims via Google Drive

1. **Upload CSV**: Place your medical claims CSV in Google Drive
2. **Get File ID**: Copy the file ID from Google Drive URL
3. **Process**: Enter file ID in the application and click "Process"
4. **Review**: Check AI reasoning and download results

### File Upload Processing

1. **Upload**: Use the file uploader in the application
2. **Configure**: Adjust processing rules if needed
3. **Process**: Click "Process Uploaded File"
4. **Download**: Get your processed Excel file with separate sheets

### Expected CSV Format

```csv
Patient ID,Claim ID,Revenue Code,HCPCS Code,Description,Service Date,Units,Charge Amount,Total Charges
P001,C001,0450,99284,ER Visit Level 4,2024-06-01,1,1200,1200
P001,C001,0300,36415,Lab Draw - CBC,2024-06-01,1,150,150
```

## 🔧 Configuration

### Environment Variables

```bash
# Google Drive API
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REFRESH_TOKEN=your_refresh_token

# Processing Rules
MAX_LINES_PER_CLAIM=28
ER_CONSOLIDATION_HOURS=24
IMAGING_GROUPING_HOURS=24

# Application Settings
ENVIRONMENT=production
LOG_LEVEL=INFO
MAX_FILE_SIZE_MB=50
```

### Custom Rules Configuration

The application supports custom processing rules:

```python
custom_rules = {
    'max_lines': 28,
    'er_consolidation': True,
    'imaging_grouping': True,
    'custom_prompt': 'Additional AI instructions...'
}
```

## 🎯 Demo Features

### Leadership Dashboard
- Real-time processing status
- File processing history
- Performance metrics
- AI reasoning insights

### Customizable Processing
- Adjustable line limits
- Configurable consolidation rules
- Custom AI prompts
- Rule override capabilities

## 🔍 AI Reasoning Engine

The AI Reasoner provides detailed explanations for all processing decisions:

- **Medical Code Analysis**: Interpretation of HCPCS, ICD, and revenue codes
- **Business Rule Applications**: Which rules were applied and why
- **Splitting Logic**: Detailed reasoning for claim divisions
- **Quality Assurance**: Validation checks and integrity verification
- **Recommendations**: Process improvement suggestions

## 📊 Output Format

Processed claims are delivered as Excel files with:

- **Separate Sheets**: Each split claim on its own sheet
- **Original Data**: All original line items preserved
- **AI Reasoning**: Detailed explanation sheet
- **Metadata**: Processing statistics and validation results

## 🚦 Quality Assurance

### Automated Checks
- Line count integrity validation
- Charge amount preservation
- 28-line limit compliance
- Service relationship maintenance

### Business Rule Validation
- ER visit consolidation verification
- Imaging service grouping confirmation
- Priority-based service ordering
- Natural break point identification

## 🛠️ Development

### Local Development

```bash
# Install in development mode
pip install -e .

# Run tests (if implemented)
python -m pytest tests/

# Start with hot reload
streamlit run app.py --server.runOnSave=true
```

### Adding New Rules

1. Extend `ClaimProcessor` class
2. Add rule logic in `_apply_business_rules`
3. Update AI reasoning in `AIReasoner`
4. Test with sample data

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- 📖 Check the [Deployment Guide](DEPLOYMENT_GUIDE.md) for setup help
- 🐛 Report issues via GitHub Issues
- 💬 Ask questions in GitHub Discussions

## 🏆 Acknowledgments

- Built with Streamlit for rapid development
- Google Drive API for seamless integration
- Pandas for robust data processing
- OpenPyXL for Excel file generation

---

**🎯 Ready to automate your medical claim processing? Get started with the deployment guide!**
