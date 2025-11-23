"""
Main application entry point for the personalized dialogue system.
Demonstrates system usage and provides CLI interface.
"""
import asyncio
import argparse
import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Add current directory to Python path to enable imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import all necessary components
try:
    from models.dialogue_models import StudentHistory, TeachingStyleConfig
    from services.llm_service import LLMConfig, ModelProvider
    from core.dialogue_processor import DialogueProcessor, DialogueBatchProcessor
    from utils.data_loader import DataLoader, DataValidator, load_student_history, load_dialogue_questions, load_system_config
    from utils.dialogue_context import DialogueContextBuilder
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you are running from the correct directory and all modules exist")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Script directory: {current_dir}")
    sys.exit(1)


def setup_logging(level: str = "INFO") -> None:
    """Set up logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('dialogue_system.log')
        ]
    )


async def process_single_dialogue(
    processor: DialogueProcessor,
    student_history: StudentHistory,
    question: str,
    expected_answer: str,
    student_answer: str,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """Process a single dialogue interaction and display results."""
    print(f"\n{'='*60}")
    print(f"QUESTION: {question}")
    print(f"EXPECTED: {expected_answer}")
    print(f"STUDENT:  {student_answer}")
    print(f"{'='*60}")
    
    try:
        # Process the dialogue turn
        dialogue_session, teacher_response, metadata = await processor.process_complete_dialogue_turn(
            student_history=student_history,
            question=question,
            expected_answer=expected_answer,
            student_answer=student_answer,
            context=context,
            update_history=True
        )
        
        # Display results
        print(f"\nJUDGMENT: {'✓ CORRECT' if metadata.get('judgment') else '✗ INCORRECT'}")
        print(f"SELECTED STYLE: {metadata.get('selected_style', 'unknown')}")
        print(f"STYLE REASON: {metadata.get('style_explanation', 'N/A')}")
        print(f"\nMISSING KNOWLEDGE:")
        print(f"  {metadata.get('missing_knowledge', 'None identified')}")
        print(f"\nTEACHER RESPONSE:")
        print(f"  {teacher_response}")
        
        if 'error' in metadata:
            print(f"\nERROR: {metadata['error']}")
        
    except Exception as e:
        print(f"\nERROR processing dialogue: {str(e)}")
        logging.error(f"Error in single dialogue processing: {str(e)}")


async def process_batch_dialogues(
    processor: DialogueProcessor,
    student_history: StudentHistory,
    batch_data: list,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """Process a batch of dialogues and display summary results."""
    print(f"\n{'='*60}")
    print(f"PROCESSING BATCH OF {len(batch_data)} DIALOGUES")
    print(f"{'='*60}")
    
    try:
        batch_processor = DialogueBatchProcessor(processor)
        
        # Fix: Prepare context with user information from CSV for each batch item
        enhanced_batch_data = []
        for item in batch_data:
            # Extract user info from CSV data and prepare context
            item_context = {
                'id': item.get('id', ''),
                'user': item.get('user', 'anonymous'),
                'difficulty': item.get('difficulty', 'medium'),
                'topic': item.get('topic', 'general'),
                'question_difficulty': item.get('difficulty', 'medium')
            }
            
            # Create enhanced item data with context
            enhanced_item = dict(item)
            enhanced_item['context'] = item_context
            enhanced_batch_data.append(enhanced_item)
        
        # Display debug information
        if enhanced_batch_data:
            first_item = enhanced_batch_data[0]
            print(f"📋 Debug: First item user = {first_item.get('user', 'NOT_FOUND')}")
            print(f"📋 Debug: First item context = {first_item.get('context', {})}")
        
        results = await batch_processor.process_batch(enhanced_batch_data, student_history, context)
        
        # Display summary
        correct_count = 0
        style_counts = {}
        
        for i, (session, response, metadata) in enumerate(results):
            is_correct = metadata.get('judgment', False)
            if is_correct:
                correct_count += 1
            
            style = metadata.get('selected_style', 'unknown')
            style_counts[style] = style_counts.get(style, 0) + 1
            
            # Show original CSV user info vs session user info
            original_user = batch_data[i].get('user', 'unknown')
            session_user = session.user if hasattr(session, 'user') else 'unknown'
            
            print(f"\n{i+1}. {'✓' if is_correct else '✗'} [{style}] {batch_data[i]['question'][:50]}...")
            print(f"   CSV User: {original_user}, Session User: {session_user}")
            print(f"   Response: {response[:100]}...")
        
        # Summary statistics
        accuracy = correct_count / len(results) if results else 0
        print(f"\n{'='*60}")
        print(f"BATCH SUMMARY:")
        print(f"  Total processed: {len(results)}")
        print(f"  Accuracy: {accuracy:.1%} ({correct_count}/{len(results)})")
        print(f"  Style distribution: {dict(style_counts)}")
        print(f"  Updated history: {len(student_history.sessions)} total sessions")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"\nERROR processing batch: {str(e)}")
        logging.error(f"Error in batch processing: {str(e)}")
        import traceback
        traceback.print_exc()


def display_student_analysis(processor: DialogueProcessor, student_history: StudentHistory) -> None:
    """Display comprehensive student analysis."""
    print(f"\n{'='*60}")
    print("STUDENT PERFORMANCE ANALYSIS")
    print(f"{'='*60}")
    
    try:
        analysis = processor.analyze_student_progress(student_history)
        
        # Performance metrics
        performance = analysis.get('performance', {})
        print(f"RECENT PERFORMANCE:")
        print(f"  Accuracy: {performance.get('accuracy', 0):.1%}")
        print(f"  Engagement: {performance.get('engagement', 0):.2f}")
        print(f"  Progress Rate: {performance.get('progress_rate', 0):+.2f}")
        
        # Learning trajectory
        trajectory = analysis.get('trajectory', {})
        print(f"\nLEARNING TRAJECTORY:")
        print(f"  Trend: {trajectory.get('trend', 0):+.3f}")
        print(f"  Consistency: {trajectory.get('consistency', 0):.2f}")
        print(f"  Recent Improvement: {trajectory.get('recent_improvement', 0):+.2f}")
        
        # Knowledge gaps
        gaps = analysis.get('knowledge_gaps', [])
        if gaps:
            print(f"\nKNOWLEDGE GAPS:")
            for gap in gaps[:5]:  # Show top 5
                print(f"  - {gap}")
        else:
            print(f"\nKNOWLEDGE GAPS: None identified")
        
        # Style effectiveness
        style_eff = analysis.get('style_effectiveness', {})
        if style_eff:
            print(f"\nSTYLE EFFECTIVENESS:")
            for style, effectiveness in sorted(style_eff.items(), key=lambda x: x[1], reverse=True):
                print(f"  {style}: {effectiveness:.1%}")
        
        print(f"\nTOTAL SESSIONS: {analysis.get('total_sessions', 0)}")
        
    except Exception as e:
        print(f"\nERROR in student analysis: {str(e)}")
        logging.error(f"Error in student analysis: {str(e)}")


def display_teaching_styles() -> None:
    """Display information about available teaching styles."""
    print(f"\n{'='*60}")
    print("AVAILABLE TEACHING STYLES")
    print(f"{'='*60}")
    
    styles = TeachingStyleConfig.get_default_styles()
    
    for style_name, config in styles.items():
        print(f"\n{style_name.upper()}:")
        print(f"  Name: {config.name}")
        print(f"  Foundation: {config.theoretical_foundation}")
        print(f"  Characteristics: {', '.join(config.characteristics)}")


async def interactive_mode(processor: DialogueProcessor) -> None:
    """Run the system in interactive mode."""
    print(f"\n{'='*60}")
    print("INTERACTIVE DIALOGUE MODE")
    print("Type 'quit' to exit, 'help' for commands")
    print(f"{'='*60}")
    
    # Create or load student history
    student_history = StudentHistory(sessions=[])
    
    while True:
        try:
            print(f"\nCommands: 'dialogue', 'analysis', 'styles', 'quit'")
            command = input("Enter command: ").strip().lower()
            
            if command in ['quit', 'exit', 'q']:
                break
            elif command in ['help', 'h']:
                print("Available commands:")
                print("  dialogue - Start a dialogue interaction")
                print("  analysis - Show student analysis")
                print("  styles   - Show teaching styles")
                print("  quit     - Exit the program")
            elif command == 'dialogue':
                question = input("Enter question: ").strip()
                if not question:
                    continue
                    
                expected = input("Enter expected answer: ").strip()
                if not expected:
                    continue
                    
                student_ans = input("Enter student answer: ").strip()
                if not student_ans:
                    continue
                
                await process_single_dialogue(
                    processor, student_history, question, expected, student_ans
                )
            elif command == 'analysis':
                display_student_analysis(processor, student_history)
            elif command == 'styles':
                display_teaching_styles()
            else:
                print("Unknown command. Type 'help' for available commands.")
                
        except KeyboardInterrupt:
            print("\nExiting interactive mode...")
            break
        except Exception as e:
            print(f"Error: {str(e)}")
            logging.error(f"Error in interactive mode: {str(e)}")


async def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(description="Personalized Dialogue System")
    parser.add_argument("--config", type=str, help="Configuration file path")
    parser.add_argument("--history", type=str, help="Student history file path")
    parser.add_argument("--questions", type=str, help="Questions file path (CSV/JSON)")
    parser.add_argument("--mode", choices=['single', 'batch', 'interactive'], 
                       default='interactive', help="Processing mode")
    parser.add_argument("--log-level", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default='INFO', help="Logging level")
    parser.add_argument("--output", type=str, help="Output file path for results")
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    try:
        # Load configuration
        if args.config:
            config_data = load_system_config(args.config)
            logger.info(f"Loaded configuration from {args.config}")
        else:
            # Default configuration
            config_data = {
                "provider": "openai",
                "model_name": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 1000,
                "service_tier": None,  # No default service tier
                "timeout": 120,
                "max_retries": 3
            }
            logger.info("Using default configuration")
        
        # Create dialogue processor
        llm_config = LLMConfig(
            provider=ModelProvider.OPENAI if config_data.get("provider", "openai").lower() == "openai" else ModelProvider.ANTHROPIC,
            model_name=config_data.get("model_name", "gpt-4"),
            temperature=config_data.get("temperature", 0.7),
            max_tokens=config_data.get("max_tokens", 1000),
            timeout=config_data.get("timeout", 120),
            max_retries=config_data.get("max_retries", 3),
            retry_delay=config_data.get("retry_delay", 2.0),
            service_tier=config_data.get("service_tier"),  # No default
            api_key=config_data.get("api_key"),
            base_url=config_data.get("base_url")
        )
        
        processor = DialogueProcessor(llm_config)
        logger.info("Dialogue processor initialized")
        
        # Load student history
        if args.history:
            student_history = load_student_history(args.history)
            logger.info(f"Loaded student history with {len(student_history)} sessions")
        else:
            student_history = StudentHistory(sessions=[])
            logger.info("Created empty student history")
        
        # Process based on mode
        if args.mode == 'interactive':
            await interactive_mode(processor)
            
        elif args.mode == 'single':
            # Single dialogue example
            await process_single_dialogue(
                processor,
                student_history,
                question="What is the capital of France?",
                expected_answer="Paris",
                student_answer="I think it's Paris, the city where the Eiffel Tower is located.",
                context={"question_difficulty": "easy"}
            )
            
        elif args.mode == 'batch':
            if not args.questions:
                logger.error("Batch mode requires --questions parameter")
                return
                
            # Load questions and process batch
            questions_data = load_dialogue_questions(args.questions)
            await process_batch_dialogues(processor, student_history, questions_data)
        
        # Save updated history if output specified
        if args.output:
            loader = DataLoader()
            loader.save_student_history_to_json(student_history, args.output)
            logger.info(f"Saved updated history to {args.output}")
        
        # Final analysis
        display_student_analysis(processor, student_history)
        
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
