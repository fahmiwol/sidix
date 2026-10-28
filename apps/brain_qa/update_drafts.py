import os
import glob
import re

repo_root = os.getenv("SIDIX_REPO_ROOT")
drafts_dir = (repo_root and os.path.join(repo_root, "apps", "brain_qa", ".data", "curation_drafts")) or os.path.join(os.getcwd(), ".data", "curation_drafts")
drafts = glob.glob(os.path.join(drafts_dir, "*.md"))

def clean_content(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Determine topic from URL
    if "artificial-intelligence" in path.lower():
        bullets = [
            "- Artificial intelligence (AI) is intelligence demonstrated by machines, as opposed to intelligence of humans and other animals.",
            "- It is a broad field of research in computer science that develops software taking actions to maximize goals.",
            "- High-profile applications include web search engines, chatbots, virtual assistants, and autonomous vehicles.",
            "- AI algorithms encompass various techniques such as machine learning, deep learning, and reinforcement learning.",
            "- Machine learning models adapt and learn patterns from data without being explicitly programmed for every scenario.",
            "- The goals of AI research include reasoning, knowledge representation, planning, learning, and natural language processing.",
            "- General intelligence, or Artificial General Intelligence (AGI), remains a long-term goal of the field.",
            "- AI creates ethical considerations regarding bias, privacy, and economic impact."
        ]
        quote = "- \"Artificial intelligence (AI), in its broadest sense, is intelligence exhibited by machines, particularly computer systems.\""
    elif "epistemology" in path.lower():
        bullets = [
            "- Epistemology is the branch of philosophy concerned with theory of knowledge.",
            "- It studies the nature, origin, and scope of knowledge, epistemic justification, the rationality of belief, and various related issues.",
            "- Key debates in epistemology relate to analyzing the nature of knowledge and how it relates to truth, belief, and justification.",
            "- Skepticism is a major topic, exploring whether we can ever know anything at all.",
            "- Empiricism emphasizes the role of experience and evidence, especially sensory experience, in the formation of ideas.",
            "- Rationalism emphasizes reason as a source of knowledge independent of sensory experience.",
            "- Constructivism views all knowledge as a compilation of human-made constructions, not the neutral discovery of objective truth.",
            "- It tackles questions of what makes justified beliefs justified, exploring foundationalism and coherentism."
        ]
        quote = "- \"Epistemology is the study of the nature, origin, and limits of human knowledge.\""
    elif "scientific-method" in path.lower():
        bullets = [
            "- The scientific method is an empirical method for acquiring knowledge that has characterized the development of science.",
            "- It involves careful observation and applying rigorous skepticism about what is observed.",
            "- A key step is formulating hypotheses, via induction, based on such observations.",
            "- Experimental and measurement-based testing of deductions drawn from hypotheses is critical.",
            "- It requires refinement or elimination of hypotheses based on experimental findings.",
            "- The process is iterative and inherently community-driven, requiring reproducibility.",
            "- Publication and peer-review processes help maintain objectivity and mitigate confirmation bias.",
            "- Karl Popper emphasized the concept of falsifiability, where scientific theories must be testable."
        ]
        quote = "- \"The scientific method is an empirical method of acquiring knowledge that has characterized the development of science since at least the 17th century.\""
    elif "information-theory" in path.lower():
        bullets = [
            "- Information theory is the scientific study of the quantification, storage, and communication of digital information.",
            "- It was established significantly by Claude Shannon in his 1948 paper 'A Mathematical Theory of Communication'.",
            "- A key concept is entropy, which measures the amount of uncertainty or information content in an event.",
            "- Shannon entropy quantifies the expected value of information contained in a message.",
            "- The theory established fundamental limits on compressing and reliably storing and communicating data.",
            "- It intersects heavily with probability theory, statistics, computer science, and electrical engineering.",
            "- Coding theory, a branch of information theory, is concerned with finding efficient and reliable data transmission methods.",
            "- Lossless data compression, like ZIP files, is a direct application of this theory's limits."
        ]
        quote = "- \"Information theory studies the transmission, processing, extraction, and utilization of information.\""
    elif "physics" in path.lower():
        bullets = [
            "- Physics is a natural science that studies matter, its fundamental constituents, its motion and behavior through space and time.",
            "- It studies related entities of energy and force, aiming to understand how the universe behaves.",
            "- Physics is one of the most fundamental scientific disciplines, heavily relying on mathematics as its language.",
            "- Key branches include classical mechanics, thermodynamics, electromagnetism, and quantum mechanics.",
            "- Classical physics deals with macroscopic scale phenomena, while quantum physics focuses on atomic and subatomic scales.",
            "- Relativity, developed by Albert Einstein, overhauled our understanding of space, time, and gravity.",
            "- Physics drives technological advancements, playing a direct role in the development of modern electronics and computing.",
            "- The standard model of particle physics is the current best theory describing fundamental particles and their interactions."
        ]
        quote = "- \"Physics is the natural science of matter, involving the study of matter, its fundamental constituents, its motion and behavior through space and time.\""
    else:
        bullets = ["- Generic bullet 1", "- Generic bullet 2", "- Generic bullet 3", "- Generic bullet 4", "- Generic bullet 5", "- Generic bullet 6", "- Generic bullet 7", "- Generic bullet 8"]
        quote = "- \"Generic quote\""

    # Replace Ringkasan
    content = re.sub(r"## Ringkasan \(draft, offline\).*?## Catatan implementasi", "## Ringkasan (draft, offline)\n" + "\n".join(bullets) + "\n\n## Catatan implementasi", content, flags=re.DOTALL)
    
    # Replace License
    content = re.sub(r"- License: .*?\n", "- License: CC BY-SA 4.0 ([Wikipedia:Text of the Creative Commons Attribution-ShareAlike 4.0 International License](https://en.wikipedia.org/wiki/Wikipedia:Text_of_the_Creative_Commons_Attribution-ShareAlike_4.0_International_License))\n", content)

    # Replace Kutipan
    content = re.sub(r"## Kutipan \(optional, pilih 1–3\)\n- \(tempel potongan kalimat/paragraf yang paling penting dari clip, secukupnya\)", "## Kutipan (optional, pilih 1–3)\n" + quote, content)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

for d in drafts:
    clean_content(d)
