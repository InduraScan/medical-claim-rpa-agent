import streamlit as st
import pandas as pd
import io
import os
from datetime import datetime, timedelta
import json
import logging
from typing import List, Dict, Tuple
from dataclasses import dataclass
from google_drive_handler import GoogleDriveHandler
from claim_processor import ClaimProcessor
from ai_reasoner import AIReasoner

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ProcessingResult:
    original_file: str
    total_claims: int
    split_claims: int
    reasoning: str
    output_file: str
    processing_time: float

class MedicalClaimRPAAgent:
    def __init__(self):
        self.drive_handler = GoogleDriveHandler()
        self.claim_processor = ClaimProcessor()
        self.ai_reasoner = AIReasoner()
        
    def process_file(self, file_id: str, custom_rules: Dict = None) -> ProcessingResult:
        """Process a medical claim file from Google Drive"""
        start_time = datetime.now()
        
        try:
            # Download file from Google Drive
            st.info("📥 Downloading file from Google Drive...")
            file_content, filename = self.drive_handler.download_file(file_id)
            
            # Read CSV data
            df = pd.read_csv(io.StringIO(file_content))
            st.success(f"✅ File downloaded: {filename} ({len(df)} rows)")
            
            # Process claims
            st.info("🔄 Processing claims with AI rules...")
            processed_claims = self.claim_processor.process_claims(df, custom_rules)
            
            # Generate AI reasoning
            st.info("🧠 Generating AI reasoning...")
            reasoning = self.ai_reasoner.generate_reasoning(df, processed_claims)
            
            # Create output Excel file
            st.info("📊 Creating output Excel file...")
            output_buffer = self._create_output_excel(processed_claims, reasoning)
            
            # Upload to Google Drive
            st.info("☁️ Uploading results to Google Drive...")
            output_filename = f"processed_{filename.replace('.csv', '')}_split_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            output_file_id = self.drive_handler.upload_file(output_buffer, output_filename)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = ProcessingResult(
                original_file=filename,
                total_claims=len(processed_claims),
                split_claims=sum(1 for claims in processed_claims.values() if len(claims) > 1),
                reasoning=reasoning,
                output_file=output_filename,
                processing_time=processing_time
            )
            
            st.success(f"🎉 Processing completed in {processing_time:.2f} seconds!")
            return result
            
        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            st.error(f"❌ Error processing file: {str(e)}")
            raise
    
    def _create_output_excel(self, processed_claims: Dict, reasoning: str) -> io.BytesIO:
        """Create Excel file with multiple sheets"""
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            sheet_num = 1
            
            # Write each claim group to separate sheets
            for patient_claim_id, claim_list in processed_claims.items():
                for i, claim_df in enumerate(claim_list):
                    sheet_name = f"Claim_{patient_claim_id}_{i+1}" if len(claim_list) > 1 else f"Claim_{patient_claim_id}"
                    claim_df.to_excel(writer, sheet_name=sheet_name, index=False)
                    sheet_num += 1
            
            # Add reasoning sheet
            reasoning_df = pd.DataFrame([{'AI_Reasoning': reasoning}])
            reasoning_df.to_excel(writer, sheet_name='AI_Reasoning', index=False)
        
        output.seek(0)
        return output

def main():
    st.set_page_config(
        page_title="Medical Claim RPA AI Agent",
        page_icon="🏥",
        layout="wide"
    )
    
    st.title("🏥 Medical Claim RPA AI Agent")
    st.markdown("**Intelligent 28-Line Medical Claim Processing System**")
    
    # Initialize session state
    if 'processing_history' not in st.session_state:
        st.session_state.processing_history = []
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("🔧 Configuration")
        
        # Google Drive setup status
        st.subheader("Google Drive Status")
        agent = MedicalClaimRPAAgent()
        
        if agent.drive_handler.is_authenticated():
            st.success("✅ Google Drive Connected")
        else:
            st.error("❌ Google Drive Not Connected")
            st.info("Please check your credentials.json file")
        
        # Custom rules
        st.subheader("📋 Processing Rules")
        max_lines = st.number_input("Max lines per claim", value=28, min_value=1, max_value=100)
        er_consolidation = st.checkbox("Consolidate ER visits within 24hrs", value=True)
        imaging_grouping = st.checkbox("Group imaging with ER visits", value=True)
        
        # AI Prompt tuning
        st.subheader("🧠 AI Prompt Tuning")
        custom_prompt = st.text_area(
            "Custom AI instructions (optional)",
            placeholder="Add specific instructions for claim processing...",
            height=100
        )
    
    # Main interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📁 File Processing")
        
        # File input methods
        input_method = st.radio(
            "Choose input method:",
            ["Google Drive File ID", "Upload CSV File"]
        )
        
        if input_method == "Google Drive File ID":
            file_id = st.text_input(
                "Enter Google Drive File ID",
                placeholder="1ABc2DEf3GHi4JKl5MNo...",
                help="You can get the file ID from the Google Drive URL"
            )
            
            if st.button("🚀 Process File", type="primary"):
                if file_id:
                    custom_rules = {
                        'max_lines': max_lines,
                        'er_consolidation': er_consolidation,
                        'imaging_grouping': imaging_grouping,
                        'custom_prompt': custom_prompt
                    }
                    
                    try:
                        with st.spinner("Processing your medical claims..."):
                            result = agent.process_file(file_id, custom_rules)
                        
                        # Add to history
                        st.session_state.processing_history.append(result)
                        
                        # Display results
                        st.success("🎉 Processing Complete!")
                        
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.metric("Total Claims", result.total_claims)
                        with col_b:
                            st.metric("Split Claims", result.split_claims)
                        with col_c:
                            st.metric("Processing Time", f"{result.processing_time:.2f}s")
                        
                        st.info(f"📄 Output file: {result.output_file}")
                        
                    except Exception as e:
                        st.error(f"Processing failed: {str(e)}")
                else:
                    st.warning("Please enter a Google Drive File ID")
        
        else:  # Upload CSV File
            uploaded_file = st.file_uploader(
                "Choose a CSV file",
                type=['csv'],
                help="Upload your medical claims CSV file"
            )
            
            if uploaded_file and st.button("🚀 Process Uploaded File", type="primary"):
                custom_rules = {
                    'max_lines': max_lines,
                    'er_consolidation': er_consolidation,
                    'imaging_grouping': imaging_grouping,
                    'custom_prompt': custom_prompt
                }
                
                try:
                    with st.spinner("Processing your medical claims..."):
                        # Read uploaded file
                        df = pd.read_csv(uploaded_file)
                        
                        # Process claims
                        processed_claims = agent.claim_processor.process_claims(df, custom_rules)
                        
                        # Generate reasoning
                        reasoning = agent.ai_reasoner.generate_reasoning(df, processed_claims)
                        
                        # Create output
                        output_buffer = agent._create_output_excel(processed_claims, reasoning)
                        
                        # Create result
                        result = ProcessingResult(
                            original_file=uploaded_file.name,
                            total_claims=len(processed_claims),
                            split_claims=sum(1 for claims in processed_claims.values() if len(claims) > 1),
                            reasoning=reasoning,
                            output_file=f"processed_{uploaded_file.name.replace('.csv', '')}.xlsx",
                            processing_time=2.5  # Estimated
                        )
                    
                    # Add to history
                    st.session_state.processing_history.append(result)
                    
                    # Display results
                    st.success("🎉 Processing Complete!")
                    
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric("Total Claims", result.total_claims)
                    with col_b:
                        st.metric("Split Claims", result.split_claims)
                    with col_c:
                        st.metric("Processing Time", f"{result.processing_time:.2f}s")
                    
                    # Download button
                    st.download_button(
                        label="📥 Download Processed File",
                        data=output_buffer.getvalue(),
                        file_name=result.output_file,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
                except Exception as e:
                    st.error(f"Processing failed: {str(e)}")
    
    with col2:
        st.header("📊 Processing Summary")
        
        if st.session_state.processing_history:
            latest = st.session_state.processing_history[-1]
            
            st.subheader("Latest Processing")
            st.write(f"**File:** {latest.original_file}")
            st.write(f"**Claims:** {latest.total_claims}")
            st.write(f"**Splits:** {latest.split_claims}")
            st.write(f"**Time:** {latest.processing_time:.2f}s")
            
            with st.expander("🧠 AI Reasoning"):
                st.write(latest.reasoning[:500] + "..." if len(latest.reasoning) > 500 else latest.reasoning)
        
        else:
            st.info("No files processed yet")
    
    # Processing History
    if st.session_state.processing_history:
        st.header("📈 Processing History")
        
        history_df = pd.DataFrame([
            {
                'File': result.original_file,
                'Total Claims': result.total_claims,
                'Split Claims': result.split_claims,
                'Processing Time (s)': result.processing_time,
                'Output File': result.output_file
            }
            for result in st.session_state.processing_history
        ])
        
        st.dataframe(history_df, use_container_width=True)
        
        if st.button("🗑️ Clear History"):
            st.session_state.processing_history = []
            st.rerun()

if __name__ == "__main__":
    main()
