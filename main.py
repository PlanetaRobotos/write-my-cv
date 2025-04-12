from openai import OpenAI
from docxtpl import DocxTemplate
from docx2pdf import convert
import os
from dotenv import load_dotenv

used_skills = set()

# Global instruction to omit branding and overly specific references.
ROLE_SYSTEM_INSTRUCTION = (
    "Write the provided role details as {count} concise sentence, maximum 120 characters. Do not provide more then 120 characters!"
    "Ensure each sentence is on a separate line!"
    "Omit any brand names, company names, product-specific details, or overly specific references. Do not mention any specific brands."
    "Each sentence must follow this structure: Action verb (Managed/Coordinated) + what you did (more detail) + (optional) reason, outcome, number."
    "Rework the following items on my resume so they match these job requirements as closely as possible. "
    "Use the same key terms as in the job posting, but maintain factual accuracy. Emphasize measurable results. "
    "Limit each paragraph to 1–2 lines. "
    "Provide half of the sentences with quantifiable metrics (e.g., 'cut load times by 30%'), "
    "and the other half describing outcomes or improvements without explicit numbers. "

    "Examples without metrics: "
    "Achieved absolute customer satisfaction by providing timely and accurate technical support for various company products (list of the products)"
    "• Streamlined asset pipeline and build processes, boosting overall efficiency and improving release frequency. "
    "• Overhauled key gameplay systems using C# best practices, enhancing framerate stability in high-load scenarios. "
    "• Provided technical mentorship and training sessions, elevating junior developers’ proficiency and reducing onboarding time. "
    "• Collaborated closely with design and QA teams, introducing a feedback loop that minimized post-release hotfixes. "

    "Examples with metrics: "
    "Spearheaded the development of modular Unity packages, reducing repetitive setup tasks by 40% and accelerating overall feature delivery. "
    "Optimized game performance through advanced profiling, cutting average load times by 30% on both Android and iOS platforms. "
    "Led a team of developers to create a scalable backend system, increasing server response times by 25% and reducing downtime by 15%. "
    "Deployed robust CI/CD pipelines for Unity projects, lowering integration failures by 80% and minimizing manual QA overhead. "

    "Maintain a professional but concise tone and incorporate my real experience with relevant details "
    "from the job posting to ensure alignment with the role."
)

ROLE_SUMMARY_INSTRUCTION = (
    "Generate a concise, achievement-oriented professional summary. "
    "Include over 5 years of experience, key accomplishments, top skills, and a short sentence on what you seek in your next role. "
    "Do not include headings, job titles, or company names. Use no more than 300 characters!"
)

default_professional_summary = (
    "Senior Unity developer with 5+ years creating scalable, high-quality titles. Proficient in C#, OOP, UI, animation, and multi-platform optimization. "
    "Eager to apply advanced design patterns and creative problem-solving to deliver out-of-the-box gaming experiences."
)

# Define role configurations.
roles_config = {
    "LUCID": {
        "count": 2,
        "instruction": (
            ROLE_SYSTEM_INSTRUCTION
        ),
        "tech_skills": False
    },
    "GALAXY": {
        "count": 4,
        "instruction": (
            ROLE_SYSTEM_INSTRUCTION
        ),
        "tech_skills": True
    },
    "WHIMSY": {
        "count": 2,
        "instruction": (
            ROLE_SYSTEM_INSTRUCTION
        ),
        "tech_skills": True
    },
    "APPSIDE": {
        "count": 1,
        "instruction": (
            ROLE_SYSTEM_INSTRUCTION
        ),
        "tech_skills": False
    },
    "WOUFF": {
        "count": 1,
        "instruction": (
            ROLE_SYSTEM_INSTRUCTION
        ),
        "tech_skills": False
    },
}

# Base instruction for generating skills.
BASE_TECH_SKILLS_INSTRUCTION = (
    "Write a list of the most important 4-7 hard (tech) skills based on the provided vacancy description. "
    "If you generated more than 7, select the most important ones. Max 7 skills!! "
    "Separate skills by ', ' with minimal punctuation. Do not use bullets or add commentary. "
    "Omit brand names, job titles, or company names, and group similar skills together. "
    "Example: C#, .NET 8, Unity, Multithreading, MS SQL, PostgreSQL, Data Structures"
)

# Define constants for skills prompts
HARD_SKILLS_PROMPT = (
    "List the top 3 logically grouped sets of technical skills extracted from the vacancy description. "
    "Each set should be a comma-separated list of related skills and appear on a separate line. "
    "Do not include bullet characters or numbering. "
    "Example:\n"
    "Unity Engine, C#, VR/AR Development, Shader Programming\n"
    "Native Plugin Integration, Performance Optimization & Analysis\n"
    "Multiplayer Networking, Cross-Platform Development\n\n"
    "Vacancy Description:\n"
)

SOFT_SKILLS_PROMPT = (
    "List the top 3 logically grouped sets of soft skills extracted from the vacancy description. "
    "Each set should be a comma-separated list of related soft skills and appear on a separate line. "
    "Do not include bullet characters or numbering. "
    "Example:\n"
    "Team Leadership, Mentoring & Training\n"
    "Strong Communication, Collaboration, Documentation\n"
    "Innovation, Accountability, Adaptability\n\n"
    "Vacancy Description:\n"
)

# Dictionary containing real experience (default info) for each role.
default_info = {
    "GALAXY": (
        "Developed engaging gameplay features for a large-scale game project, leveraging .NET to create interactive and dynamic player experiences. "
        "Built responsive user interfaces and modular packages using .NET technologies, streamlining workflows and enhancing team productivity. "
        "Optimized performance across multiple devices with .NET-based solutions to ensure a smooth and engaging user experience."
    ),
    "WHIMSY": (
        "Developed core systems for an online multiplayer game focusing on scalability, seamless player interactions, and high-performance networking solutions. "
        "Integrated innovative game elements using .NET-based frameworks to boost engagement and support long-term growth."
    ),
    "APPSIDE": (
        "Engineered reusable game systems for hyper-casual and casual titles, streamlining development workflows and ensuring high-quality, timely delivery. "
    ),
    "WOUFF": (
        "Developed casual and WebGL outsourcing games, crafting foundational systems and optimizing legacy code to enhance performance and functionality."
    ),
    "LUCID": (
        "Led the development of a VR therapeutic application for autistic children, enabling simple task training with an AI-driven prompting system optimized for Quest devices to enhance engagement and learning outcomes."
        "Architected a scenario-based guidance system with configurable, flexible scenarios to provide adaptive and personalized training experiences."
        "Implemented dynamic VR avatars with inverse kinematics (IK) to ensure accurate and natural user representation, supporting customizable avatars for a more immersive experience."
    )
}


def build_skills_instruction(vacancy_text, used_skills_list):
    """
    Combines the base tech skills instruction with a mention
    of already used skills, instructing the model not to repeat them.
    """
    # Turn the set into a comma-separated string (or any format you prefer).
    used_str = ", ".join(sorted(used_skills_list))

    # Additional instruction to the model:
    additional_prompt = ""
    if used_str:
        additional_prompt = (
            "\n\nAvoid repeating these skills that have already been listed: "
            f"{used_str}"
        )

    # Combine everything into one final instruction.
    return BASE_TECH_SKILLS_INSTRUCTION + additional_prompt + "\n\nVacancy Description:\n" + vacancy_text


def deduplicate_skills(skills_string, used_skills_set):
    """
    Splits the comma-separated skill list, removes duplicates, and returns
    a comma-separated string of unique skills. Also updates the used_skills_set.
    """
    raw_skills = [s.strip() for s in skills_string.split(",")]
    new_skills = []

    for skill in raw_skills:
        skill_lower = skill.lower()
        if skill_lower not in used_skills_set:
            new_skills.append(skill)
            used_skills_set.add(skill_lower)

    return ", ".join(new_skills)


def rewrite_text_with_llm(input_text, field_name, custom_instruction, vacancy_text=""):
    """
    Uses the OpenAI ChatCompletion API to rewrite the provided text.
    If vacancy_text is provided, it will be included in the prompt for context.
    """
    additional_context = f"\n\nVacancy Description:\n{vacancy_text}" if vacancy_text else ""

    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant that produces concise, professional, achievement-oriented content without extraneous commentary."
            )
        },
        {
            "role": "user",
            "content": (
                f"{custom_instruction}\n\n"
                f"Field: {field_name}\n"
                f"Role Description:\n{input_text}{additional_context}\n\n"
                "Rewritten version:"
            )
        }
    ]

    client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
    )

    chat_completion = client.chat.completions.create(
        messages=messages,
        model="gpt-4o",
        temperature=0.7,
        # max_tokens=300
    )

    rewritten_text = chat_completion.choices[0].message.content
    return rewritten_text


def update_cv_template(context):
    """
    Loads the DOCX template and fills in placeholders with the updated text.
    """
    template_path = "CV_template.docx"
    output_docx_path = "CV.docx"

    doc = DocxTemplate(template_path)
    doc.render(context)
    doc.save(output_docx_path)
    return output_docx_path


def convert_docx_to_pdf(input_docx, output_pdf="CV_final.pdf"):
    """
    Converts the updated DOCX file to a PDF.
    """
    convert(input_docx, output_pdf)
    return output_pdf


def main():
    context = {}
    # Load the vacancy description once.
    with open("vacancy_description.txt", "r", encoding="utf-8") as f:
        vacancy_text = f.read()

    # Process each role for responsibilities.
    for role, config in roles_config.items():
        # Use the real experience from the default_info dictionary.
        role_description = default_info.get(role, "")
        if not role_description:
            print(f"Warning: No default info found for role {role}.")

        # Format the instruction with the required count.
        instruction = config["instruction"].format(count=config["count"])
        print(f"\nProcessing role {role} responsibilities...")
        updated_text = rewrite_text_with_llm(role_description, f"ROLE_DESCRIPTION_{role}", instruction, vacancy_text)

        # Split the result into sentences (each sentence is on a separate line).
        sentences = [line.strip() for line in updated_text.splitlines() if line.strip()]
        # Assign each sentence to its corresponding placeholder.
        for i in range(config["count"]):
            if i < len(sentences):
                context[f"ROLE_DESCRIPTION_{role}_{i}"] = sentences[i]
                print(f"Set ROLE_DESCRIPTION_{role}_{i}: {sentences[i]}")
            else:
                context[f"ROLE_DESCRIPTION_{role}_{i}"] = ""
                print(f"Warning: Expected {config['count']} sentences but got fewer for role {role}.")

        # For roles that require tech skills, generate skills using the combined approach.
        if config["tech_skills"]:
            print(f"\nProcessing tech skills for role {role}...")
            # Build the final prompt including already used skills.
            final_skills_prompt = build_skills_instruction(vacancy_text, used_skills)
            updated_skills = rewrite_text_with_llm("", f"ROLE_DESCRIPTION_{role}_SKILLS", final_skills_prompt)
            deduped_skills = deduplicate_skills(updated_skills.strip(), used_skills)
            context[f"ROLE_DESCRIPTION_{role}_SKILLS"] = deduped_skills
            print(f"Set ROLE_DESCRIPTION_{role}_SKILLS: {deduped_skills}")

    # Generate professional summary using the LLM.
    professional_summary = rewrite_text_with_llm(
        default_professional_summary,
        "ROLE_SUMMARY",
        ROLE_SUMMARY_INSTRUCTION,
        vacancy_text  # Pass the vacancy description if desired for context.
    )

    role_hard_skills = rewrite_text_with_llm("", "ROLE_HARD_SKILLS", HARD_SKILLS_PROMPT + vacancy_text)
    context["ROLE_HARD_SKILLS"] = role_hard_skills.strip()

    role_soft_skills = rewrite_text_with_llm("", "ROLE_SOFT_SKILLS", SOFT_SKILLS_PROMPT + vacancy_text)
    context["ROLE_SOFT_SKILLS"] = role_soft_skills.strip()

    # Print the generated professional summary.
    print(f"\nGenerated professional summary:\n{professional_summary}")

    # Add the generated professional summary to your context.
    context["ROLE_SUMMARY"] = professional_summary.strip()

    # Update the DOCX template with the new content.
    print("\nUpdating DOCX template with the new content...")
    filled_docx = update_cv_template(context)
    print(f"Process complete. Your updated CV DOCX is saved as: {filled_docx}")

    # Optionally convert the DOCX to PDF.
    # pdf_file = convert_docx_to_pdf(filled_docx)
    # print(f"Process complete. Your updated CV PDF is saved as: {pdf_file}")


if __name__ == "__main__":
    main()
