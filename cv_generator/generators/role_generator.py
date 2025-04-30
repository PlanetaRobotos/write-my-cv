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
        """Extract key technical terms and achievement patterns from the job description."""
        if not self.vacancy_text:
            return []

        prompt = (
            "Analyze this job description and extract TWO TYPES of information:\n"
            "1. The top 12 TECHNICAL KEYWORDS/SKILLS that are crucial for this role\n"
            "2. The top 3 ACHIEVEMENT PATTERNS/METRICS that the employer values\n\n"
            "Return a JSON object with two arrays:\n"
            "{\n"
            "  \"technical_keywords\": [\"Unity\", \"C#\", \"SOLID principles\", ...],\n"
            "  \"achievement_patterns\": [\"performance optimization\", \"team leadership\", ...]\n"
            "}\n\n"
            f"Job Description:\n{self.vacancy_text}"
        )

        messages = [
            {"role": "system",
             "content": "You extract key information from job descriptions to craft targeted resumes."},
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
            # For backward compatibility, we'll continue using job_keywords
            return result.get("technical_keywords", [])
        except Exception as e:
            print(f"Error extracting job keywords: {e}")
            return []

    def _create_role_context(self):
        """Create a contextual overview showing clear career progression."""
        career_context = "CAREER PROGRESSION (Most Recent First):\n\n"

        # Define clear seniority levels for each role
        seniority_mapping = {
            "LUCID": "Senior/Lead Developer Role",
            "GALAXY": "Senior Developer Role",
            "WHIMSY": "Mid-Level Developer Role",
            "APPSIDE": "Junior-Mid Developer Role",
            "WOUFF": "Junior Developer Role"
        }

        for role, config in self.roles_config.items():
            default_info = [desc.strip() for desc in self.default_info.get(role, '').split(',') if desc.strip()]
            career_context += f"{role} ({seniority_mapping[role]}):\n"
            for desc in default_info:
                career_context += f"- {desc}\n"
            career_context += "\n"
        return career_context

    def generate(self):
        """Generate role descriptions with awareness of the entire career progression."""
        career_context = self._create_role_context()
        processed_keywords = set()
        ordered_roles = ["WOUFF", "APPSIDE", "WHIMSY", "GALAXY", "LUCID"]
        attempts_per_role = {}  # Track how many attempts per role

        for role in ordered_roles:
            attempts_per_role[role] = 0
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

            # Generate description with retry logic
            self._generate_role_description(role, career_context, role_description,
                                            count, half_count, priority_keywords)

            # If no valid descriptions were generated, retry with different temperature
            max_attempts = 3
            while (role not in self.role_descriptions or not self.role_descriptions[role] or
                   len(self.role_descriptions[role]) < count) and attempts_per_role[role] < max_attempts:
                attempts_per_role[role] += 1
                print(f"Retrying generation for {role} (attempt {attempts_per_role[role]})")

                # Adjust temperature and top keyword selection based on attempt number
                temperature = 0.7 + (attempts_per_role[role] * 0.1)  # Increase randomness
                keyword_count = 5 + attempts_per_role[role]  # Use more keywords
                retry_keywords = self.job_keywords[:keyword_count]

                self._generate_role_description(role, career_context, role_description,
                                                count, half_count, retry_keywords,
                                                temperature=temperature)

            # Store descriptions in context with proper template tags
            descriptions = self.role_descriptions.get(role, [])
            for i, desc in enumerate(descriptions):
                self.context[f"ROLE_DESCRIPTION_{role}_{i}"] = desc

            # Update processed keywords
            for point in self.role_descriptions.get(role, []):
                for keyword in self.job_keywords:
                    if keyword.lower() in point.lower():
                        processed_keywords.add(keyword.lower())

        return self.role_descriptions, self.selected_role_keywords

    def _generate_role_description(self, role, career_context, role_description,
                                   count, half_count, priority_keywords, temperature=0.7):
        """Generate description for a specific role."""
        # Define seniority level based on role
        seniority_mapping = {
            "LUCID": "Senior/Lead Developer",
            "GALAXY": "Senior Developer",
            "WHIMSY": "Mid-Level Developer",
            "APPSIDE": "Junior-Mid Developer",
            "WOUFF": "Junior Developer"
        }

        seniority_level = seniority_mapping.get(role, "Developer")

        ROLE_SYSTEM_INSTRUCTION = """
        You are an expert CV writer crafting a Unity Developer's work experience that will STAND OUT and get interviews.

        Create {count} powerful bullet points for the {role} position ({seniority_level}).

        EACH BULLET POINT MUST:
        1. Start with a STRONG ACTION VERB (engineered, optimized, architected, designed)
        2. Show what YOU DID, not what you were responsible for
        3. Include at least one SPECIFIC, IMPRESSIVE METRIC that can be highlighted
        4. Follow one of these story patterns:
           - REACHING NEW HEIGHTS: Show achievement of a big, round number milestone
           - TURNAROUND STORY: Show how you overcame specific obstacles to achieve success 
           - FIRSTS: Highlight something you did that had never been done before
        5. Include these keywords across all bullets: {keywords}

        FOR MAXIMUM SCANNABILITY:
        Put <BOLD> tags around the most important parts:
          - <BOLD>Key metrics and numbers</BOLD>
          - <BOLD>Technical achievements</BOLD> and specialized skills
          
        STUDY THIS HIGHLIGHTING PATTERN:
        * <BOLD>First of only 2 temporary employees hired</BOLD> out of a group in excess of 60 customer service representatives
        * Awarded <BOLD>Representative of the Month</BOLD> on no less than five occasions
        * Redefined quality standards with monthly <BOLD>monitoring scores of 93% and higher</BOLD>
        * <BOLD>Mentored struggling representatives</BOLD> to increase their call monitoring performance
        * <BOLD>Promoted twice</BOLD> from Tip Writer, to CS Web Technologist, to CS Web Specialist

        FORMAT REQUIREMENTS:
        - Maximum 120 characters per bullet point
        - No bullet points/dashes/hyphens at the beginning
        - No periods at the end
        - Don't highlight more than 30% of the text
        - Be consistent with formatting style within each bullet point

        CREATE BULLETS THAT:
        - Tell a COMPLETE STORY of achievement, not just responsibilities
        - Put the most impressive information UP FRONT
        - Show TECHNICAL COMPLEXITY and your unique contribution
        - Would make a hiring manager think "This person gets results"
        """

        instruction = ROLE_SYSTEM_INSTRUCTION.format(
            count=count,
            role=role,
            seniority_level=seniority_level,
            keywords=", ".join(priority_keywords)
        )

        messages = [
            {"role": "system", "content": instruction},
            {"role": "user", "content":
                f"Career Context:\n{career_context}\n\n"
                f"Role to describe: {role} ({seniority_level})\n\n"
                f"Role Description:\n{role_description}\n\n"
                f"Job Description:\n{self.vacancy_text}\n\n"
                f"Write exactly {count} bullet points with appropriate <BOLD> tags."
                f"Each should start with an action verb and include at least one specific metric."
             }
        ]

        try:
            print(f"Generating descriptions for {role} with temperature {temperature}")
            response = self.client.chat.completions.create(
                messages=messages,
                model="gpt-4o",
                temperature=temperature
            )

            bullet_points = self._process_response(response, role)

            # If we already have some descriptions for this role, extend rather than replace
            if role in self.role_descriptions and self.role_descriptions[role]:
                current_points = len(self.role_descriptions[role])
                needed_points = count - current_points

                if needed_points > 0 and bullet_points:
                    self.role_descriptions[role].extend(bullet_points[:needed_points])
            else:
                self.role_descriptions[role] = bullet_points

            # Log success or issues
            if not bullet_points:
                print(f"WARNING: No valid bullet points generated for {role}")
                print(f"Raw response: {response.choices[0].message.content[:200]}...")
            else:
                print(f"Successfully generated {len(bullet_points)} points for {role}")

        except Exception as e:
            print(f"Error generating descriptions for {role}: {e}")
            # Only set default error message if no descriptions exist yet
            if role not in self.role_descriptions or not self.role_descriptions[role]:
                self.role_descriptions[role] = ["Error generating description"] * count

    def _process_response(self, response, role):
        """Process the response to get clean bullet points with proper formatting."""
        bullet_points = []
        raw_text = response.choices[0].message.content

        # Log the raw response for debugging
        print(f"Raw response for {role} (first 100 chars): {raw_text[:100]}...")

        # Split by line breaks and clean up
        lines = [line.strip() for line in raw_text.split('\n') if line.strip()]

        # Keep track of valid and invalid lines for logging
        valid_lines = []
        rejected_lines = []

        # Filter and process the lines
        for line in lines:
            original_line = line

            # Remove any bullet point markers, numbers or dashes
            if line.startswith('- '):
                line = line[2:].strip()
            elif line.startswith('• '):
                line = line[2:].strip()
            elif line.startswith('* '):
                line = line[2:].strip()
            elif len(line) > 2 and line[0].isdigit() and line[1:].startswith('. '):
                line = line[line.find('.') + 1:].strip()
            elif len(line) > 3 and line[0].isdigit() and line[1].isdigit() and line[2:].startswith('. '):
                line = line[line.find('.') + 1:].strip()

            # Remove any trailing periods
            if line.endswith('.'):
                line = line[:-1]

            # Skip very short lines or headers
            if len(line) < 10:
                rejected_lines.append(f"Too short: {original_line}")
                continue

            # Skip if it looks like a header or title (all caps, no formatting)
            if line.isupper() and not re.search(r'<BOLD>|</BOLD>|\*\*', line):
                rejected_lines.append(f"Looks like header: {original_line}")
                continue

            # Normalize bold tags - handle both HTML-style tags and markdown-style asterisks
            # First normalize BOLD tags
            line = re.sub(r'<\s*BOLD\s*>', '<BOLD>', line, flags=re.IGNORECASE)
            line = re.sub(r'<\s*/\s*BOLD\s*>', '</BOLD>', line, flags=re.IGNORECASE)
            line = re.sub(r'<\s*B\s*>', '<BOLD>', line, flags=re.IGNORECASE)
            line = re.sub(r'<\s*/\s*B\s*>', '</BOLD>', line, flags=re.IGNORECASE)

            # Now handle **bold** markdown format
            # Convert ** to <BOLD> tags while being careful with spacing
            asterisk_pattern = r'\*\*(.*?)\*\*'
            while re.search(asterisk_pattern, line):
                match = re.search(asterisk_pattern, line)
                if match:
                    bold_text = match.group(1)
                    line = line.replace(f"**{bold_text}**", f"<BOLD>{bold_text}</BOLD>")

            # Clean up any mismatched tags
            open_tags = len(re.findall(r'<BOLD>', line))
            close_tags = len(re.findall(r'</BOLD>', line))

            if open_tags > close_tags:
                line += '</BOLD>' * (open_tags - close_tags)
            elif close_tags > open_tags:
                line = '<BOLD>' * (close_tags - open_tags) + line

            # Check for any non-BOLD HTML tags that might cause issues
            if re.search(r'<(?!BOLD|/BOLD)[^>]+>', line):
                # Instead of rejecting, try to clean these up
                line = re.sub(r'<(?!BOLD|/BOLD)[^>]+>', '', line)

            valid_lines.append(line)
            bullet_points.append(line)

        # Log results for debugging
        print(f"Found {len(valid_lines)} valid lines for {role}")
        if rejected_lines:
            print(f"Rejected {len(rejected_lines)} lines for {role}")

        # If all lines were filtered out but we have original content, make a best effort
        if not bullet_points and lines:
            print(f"All lines were filtered out for {role}, attempting to recover...")
            # Take the longest lines as a fallback
            lines.sort(key=len, reverse=True)
            bullet_points = [line.strip() for line in lines[:5] if len(line) > 15]

        return bullet_points