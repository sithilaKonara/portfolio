(function() {
  // Wait for the DOM to be ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  function init() {
    const input = document.getElementById('terminalInput');
    const output = document.getElementById('output');
    const terminalBody = document.getElementById('terminalBody');

    if (!input || !output) return;

    let commandHistory = [];
    let historyIndex = -1;

    // Command definitions
    const commands = {
      help: `
  Available commands:
    whoami      - About me
    experience  - Work experience summary
    skills      - Core competencies
    certs       - Certifications
    education   - Education background
    contact     - Get in touch
    clear       - Clear terminal
    status      - Current availability
    blog        - Latest writings
  `,

      whoami: `
  👤 Sithila Konara
  Cloud, DevOps, Platform & SRE Engineer
  📍 Turku, Finland
  ⚡ 12 years in the industry
  🏗️ Building resilient, self-healing distributed systems with observerbility
  `,

      experience: `
  💼 Experience Summary:

  🔹 HCLTECH (2024 - Present)
     Site Reliability Engineer

  🔹 PEARSON (2022 - 2023)
     Associate Technical Specialist

  🔹 PEARSON (2018 - 2022)
     Senior System Engineer

  🔹 INVOLVE 360 (2016 - 2018)
     Infrastructure Management Engineer

  🔹 Systems Engineer (2015 - 2016)
     Systems Engineer

  🔹 System Support Technician (2013 - 2015)
     System Support Technician
  `,

      skills: `
  🛠️ Core Competencies:

  ☁️  Cloud Platforms: AWS, GCP
  📦  Container Orchestration: Kubernetes, Docker
  🏗️  Infrastructure as Code: Terraform, Ansible
  🔧  Automation: Python, Bash, GitHub Actions
  🔐  Security: IAM, Vault, Least-Privilege Access
  📊  Observability: Monitoring, Dashboards, SLO Tracking
  💰  FinOps: Cost Optimization, Resource Visibility
  `,

      certs: `
  📜 Certifications:

  ✅ AWS Certified Solution Architect - Associate
  ✅ HashiCorp Certified: Terraform Associate (002)
  ✅ Red Hat Certified Engineer (RHCE)
  `,

      education: `
  🎓 Education:

  📚 Master of Information Security (MIS)
     University of Colombo School of Computing (2020)

  🎓 BSc Special (Hons) in Information Technology
     Sri Lanka Institute of Information Technology (2014)
  `,

      contact: `
  📬 Connect with me:

  📧 Email: kmsithila@gmail.com
  📱 Phone: +358 417 241 555
  📍 Location: Turku, Finland

  🔗 LinkedIn: https://www.linkedin.com/in/sithila-konara/
  💻 GitHub: https://github.com/sithilaKonara
  `,

      status: `
  🟢 STATUS: OPEN TO OPPORTUNITIES

  Currently seeking:

    • Cloud Positions
    • DevOps Positions
    • Platform Engineering Roles
    • SRE Roles

  Ready to build resilient systems at scale!
  `,

      blog: `
  📝 Latest Writings:

    Ⓜ  Medium: https://medium.com/@sithila_92123

  → Read all: /articles
  `
    };

    function executeCommand(command) {
      if (!output) return;

      // Remove the typewriter cursor line (last line)
      const lastLine = output.lastElementChild;
      if (lastLine && lastLine.querySelector('.typewriter')) {
        lastLine.remove();
      }

      // Add the command line
      const cmdLine = document.createElement('div');
      cmdLine.className = 'line';
      cmdLine.innerHTML = `<span class="prompt">❯</span> <span class="text-white">${command}</span>`;
      output.appendChild(cmdLine);

      // Add the response
      const respLine = document.createElement('div');
      respLine.className = 'line';

      if (command === 'clear') {
        output.innerHTML = '';
        // Add a fresh prompt
        const promptLine = document.createElement('div');
        promptLine.className = 'line';
        promptLine.innerHTML = `<span class="prompt">❯</span> <span class="text-primary-container typewriter">Ready for input_</span>`;
        output.appendChild(promptLine);
        if (terminalBody) terminalBody.scrollTop = terminalBody.scrollHeight;
        return;
      }

      const response = commands[command] || `Command not found: "${command}". Type 'help' for available commands.`;
      respLine.innerHTML = `<span class="text-secondary-container" style="white-space: pre-wrap;">${response}</span>`;
      output.appendChild(respLine);

      // Add the prompt for next command
      const newPrompt = document.createElement('div');
      newPrompt.className = 'line';
      newPrompt.innerHTML = `<span class="prompt">❯</span> <span class="text-primary-container typewriter">Ready for input_</span>`;
      output.appendChild(newPrompt);

      // Scroll to bottom
      if (terminalBody) terminalBody.scrollTop = terminalBody.scrollHeight;
    }

    // Focus input on click anywhere in terminal
    const terminalContainer = document.getElementById('terminalContainer');
    if (terminalContainer) {
      terminalContainer.addEventListener('click', function() {
        input.focus();
      });
    }

    input.addEventListener('keydown', function(e) {
      if (e.key === 'Enter') {
        const command = input.value.trim().toLowerCase();
        if (command) {
          commandHistory.push(command);
          historyIndex = commandHistory.length;
          executeCommand(command);
        }
        input.value = '';
        // Auto-scroll
        terminalBody.scrollTop = terminalBody.scrollHeight;
      }

      // Command history (up/down arrows)
      if (e.key === 'ArrowUp') {
        e.preventDefault();
        if (historyIndex > 0) {
          historyIndex--;
          input.value = commandHistory[historyIndex];
        }
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        if (historyIndex < commandHistory.length - 1) {
          historyIndex++;
          input.value = commandHistory[historyIndex];
        } else {
          historyIndex = commandHistory.length;
          input.value = '';
        }
      }
    });
  }
})();