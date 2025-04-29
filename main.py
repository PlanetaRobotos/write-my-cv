from cv_generator.cv_generator import CVGenerator
from dotenv import load_dotenv
import os

def main():
    # Load environment variables
    load_dotenv()

    # Check if API key is available
    if not os.environ.get("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found in environment variables.")
        print("Please set your OpenAI API key in a .env file or directly in the environment.")
        exit(1)

    # Check if vacancy description exists
    if not os.path.exists("vacancy_description.txt"):
        print("Warning: 'vacancy_description.txt' not found. Please create this file with the job description.")
        # Create an empty file as a placeholder
        with open("vacancy_description.txt", "w", encoding="utf-8") as f:
            f.write("Please replace this with the actual job description.")
        print("Created an empty placeholder file. Please add the job description and run again.")
        exit(1)

    # Check if CV template exists
    if not os.path.exists("CV_template.docx"):
        print("Error: 'CV_template.docx' not found. Please ensure your CV template is in the current directory.")
        exit(1)

    print("\n=== Starting CV Generation ===")
    print("This process will analyze the job description and update your CV to match the requirements.")

    try:
        # Initialize and run the CV generator
        cv_generator = CVGenerator()
        
        # Run the interactive menu
        while True:
            if not cv_generator.generate_cv():
                break
            
            # Ask if user wants to generate more sections
            choice = input("\nGenerate more sections? (y/n): ").strip().lower()
            if choice != 'y':
                break

        # Print generated content for review
        print("\n=== Generated Content Review ===")
        print("\n=== Role Descriptions ===")
        for role, descriptions in cv_generator.role_descriptions.items():
            print(f"\n{role}:")
            for i, desc in enumerate(descriptions):
                print(f"  {i + 1}. {desc}")

        print("\n=== Professional Summary ===")
        print(cv_generator.context.get("ROLE_SUMMARY", "No summary generated"))

        print("\n=== Skills ===")
        print(f"Programming: {cv_generator.context.get('ROLE_SKILLS_PROGRAMMING', 'None generated')}")
        print(f"Technical: {cv_generator.context.get('ROLE_SKILLS_TECHNICAL', 'None generated')}")
        print(f"Soft Skills: {cv_generator.context.get('ROLE_SKILLS_SOFT', 'None generated')}")

        print("\n=== Self-Study Entries ===")
        print(f"Self-Study 0: {cv_generator.context.get('SELF_STUDY_0', 'No entry generated')}")
        print(f"Self-Study 1: {cv_generator.context.get('SELF_STUDY_1', 'No entry generated')}")

        print("\n=== CV Generation Complete ===")
        print("Your updated CV has been saved as 'CV.docx'")

    except Exception as e:
        print(f"\nError during CV generation: {e}")
        import traceback
        traceback.print_exc()
        print("\nPlease check your inputs and try again.")

if __name__ == "__main__":
    main()