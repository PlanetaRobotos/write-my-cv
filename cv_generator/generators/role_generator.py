import json
import re
from ..base_generator import BaseGenerator


class RoleGenerator(BaseGenerator):
    def __init__(self, vacancy_text, default_info, roles_config, api_key=None):
        super().__init__(api_key)
        self.vacancy_text = vacancy_text
        self.default_info = default_info
        self.roles_config = roles_config
        self.role_descriptions = {}
        self.selected_role_keywords = {}
        self.job_keywords = self._extract_job_keywords()

    def _extract_job_keywords(self):
        """Extract key technical terms from the job description."""
        if not self.vacancy_text:
            return []

        prompt = (
            "Extract the top 15 most important technical keywords/skills from this job description. "
            "Return only a JSON array of strings with no explanation. "
            "Focus on specific technologies, frameworks, and methodologies. "
            "Example format: {\"keywords\": [\"Unity\", \"C#\", \"SOLID principles\", \"Multiplayer development\"]}\n\n"
            f"Job Description:\n{self.vacancy_text}"
        )

        messages = [
            {"role": "system",
             "content": "You extract technical keywords from job descriptions and return them as a JSON array."},
            {"role": "user", "content": prompt}
        ]

        try:
            response = self.client.chat.completions.create(
                messages=messages,
                model="gpt-4o",
                response_format={"type": "json_object"},
                temperature=0.2
            )
            result = json.loads(response.choices[0].message.content)
            return result.get("keywords", [])
        except Exception as e:
            print(f"Error extracting job keywords: {e}")
            return []

    def _create_role_context(self):
        """Create a contextual overview of all roles."""
        career_context = "Career Progression Overview:\n\n"
        for role, config in self.roles_config.items():
            # Split the default info by comma and clean up
            default_info = [desc.strip() for desc in self.default_info.get(role, '').split(',') if desc.strip()]
            career_context += f"{role}:\n"
            for desc in default_info:
                career_context += f"- {desc}\n"
            career_context += "\n"
        return career_context

    def generate(self):
        """Generate role descriptions with awareness of the entire career progression."""
        career_context = self._create_role_context()
        processed_keywords = set()
        ordered_roles = ["WOUFF", "APPSIDE", "WHIMSY", "GALAXY", "LUCID"]

        for role in ordered_roles:
            config = self.roles_config[role]
            role_description = self.default_info.get(role, "")
            count = config["count"]
            half_count = max(1, count // 2)

            # Select priority keywords for this role
            if role in ["GALAXY", "LUCID"]:
                priority_keywords = self.job_keywords[:5]
            else:
                available_keywords = [k for k in self.job_keywords if k.lower() not in processed_keywords]
                if len(available_keywords) < 5:
                    additional_keywords = self.job_keywords[:5]
                    priority_keywords = list(set(available_keywords + additional_keywords))[:5]
                else:
                    priority_keywords = available_keywords[:5]

            self.selected_role_keywords[role] = priority_keywords

            # Generate description
            self._generate_role_description(role, career_context, role_description,
                                            count, half_count, priority_keywords)

            # Store descriptions in context with proper template tags
            descriptions = self.role_descriptions.get(role, [])
            for i, desc in enumerate(descriptions):
                self.context[f"ROLE_DESCRIPTION_{role}_{i}"] = desc

            # Update processed keywords
            for point in self.role_descriptions[role]:
                for keyword in self.job_keywords:
                    if keyword.lower() in point.lower():
                        processed_keywords.add(keyword.lower())

        # Apply Word formatting to the document
        if hasattr(self, 'document'):
            self.format_document_with_bold(self.document)

        return self.role_descriptions, self.selected_role_keywords

    def _generate_role_description(self, role, career_context, role_description,
                                   count, half_count, priority_keywords):
        """Generate description for a specific role."""
        ROLE_SYSTEM_INSTRUCTION = """
        You are an expert CV writer crafting a Unity Developer's work experience that STANDS OUT to hiring managers.

        Your task:
        1. Write {count} powerful bullet points (120 characters max each) for the {role} position.
        2. Start each bullet with a STRONG ACTION VERB (no dash/hyphen prefix).
        3. Focus on OUTCOMES and IMPACT - not just responsibilities.
        4. For each bullet point, follow this pattern: ACTION + CHALLENGE/CONTEXT + RESULT with metrics.
        5. Include these keywords across your bullet points: {keywords}.

        Each bullet point must tell ONE of these three story types:
        - REACHING NEW HEIGHTS: Show quantifiable achievements with impressive metrics
        - TURNAROUND STORIES: Describe obstacles overcome to achieve success
        - FIRSTS: Highlight pioneering work or innovation never done before

        Important rules:
        - Include ONE clear metric in each bullet point (e.g., 30%, 2x, 5 seconds)
        - Be SPECIFIC with numbers to allow for proper formatting later
        - Show COMPLEXITY - hint at the challenging environment you succeeded in
        - NO generic job descriptions - only YOUR unique accomplishments
        - Do NOT use asterisks for emphasis - metrics will be formatted later
        """

        instruction = ROLE_SYSTEM_INSTRUCTION.format(
            count=count,
            role=role,
            keywords=", ".join(priority_keywords)
        )

        messages = [
            {"role": "system", "content": instruction},
            {"role": "user",
             "content": f"Career Context:\n{career_context}\n\nRole to describe: {role}\n\nRole Description:\n{role_description}\n\nJob Description:\n{self.vacancy_text}\n\nWrite {count} bullet points:"}
        ]

        try:
            response = self.client.chat.completions.create(
                messages=messages,
                model="gpt-4o",
                temperature=0.7
            )

            bullet_points = self._process_response(response)
            self.role_descriptions[role] = bullet_points

        except Exception as e:
            print(f"Error generating descriptions for {role}: {e}")
            self.role_descriptions[role] = ["Error generating description"] * count

    def _process_response(self, response):
        """Process the response to get clean bullet points with metrics identified."""
        bullet_points = []
        raw_text = response.choices[0].message.content

        # Split by line breaks and clean up
        for line in raw_text.split('\n'):
            line = line.strip()

            # Skip empty lines or lines that start with dashes
            if not line or line.startswith('-'):
                continue

            # Remove any trailing periods
            if line.endswith('.'):
                line = line[:-1]

            # Keep lines that start with action verbs (not bullets/numbers)
            if line and not line[0].isdigit() and not line.startswith('-'):
                # Identify metrics for later Word formatting
                line = self._mark_metrics_for_formatting(line)
                bullet_points.append(line)

        return bullet_points

    def _mark_metrics_for_formatting(self, text):
        """Mark metrics in text for later Bold formatting in Word."""
        # Common metric patterns (percentages, multipliers, time measurements)
        patterns = [
            r'(\d+%)',  # Percentage (e.g., 30%)
            r'(\d+x)',  # Multiplier (e.g., 5x)
            r'(\d+\s*(?:seconds|minutes|hours|days|weeks|months))',  # Time
            r'(\$\d+(?:[KMB])?)',  # Money (e.g., $10K, $5M)
            r'((?:increased|decreased|reduced|improved|boosted|enhanced)\s+by\s+\d+%)',  # Changes
        ]

        # Add a marker around metrics for your document processor
        for pattern in patterns:
            text = re.sub(pattern, r'<BOLD>\1</BOLD>', text)

        return text

    def format_document_with_bold(self, document):
        """Apply proper Word formatting based on markers."""
        for role, descriptions in self.role_descriptions.items():
            for i, desc in enumerate(descriptions):
                # Extract parts to be bold
                bold_parts = re.findall(r'<BOLD>(.*?)</BOLD>', desc)

                # Remove markers for clean text
                clean_desc = re.sub(r'<BOLD>(.*?)</BOLD>', r'\1', desc)

                # Add bullet point to document
                paragraph = document.add_paragraph()
                paragraph.style = 'List Bullet'

                # Process text to add proper Bold formatting
                remaining_text = clean_desc
                for bold_part in bold_parts:
                    parts = remaining_text.split(bold_part, 1)
                    if len(parts) > 1:
                        # Add normal text
                        paragraph.add_run(parts[0])
                        # Add bold text
                        paragraph.add_run(bold_part).bold = True
                        # Update remaining text
                        remaining_text = parts[1]
                    else:
                        # No more occurrences of this bold part
                        break

                # Add any remaining text
                if remaining_text:
                    paragraph.add_run(remaining_text)