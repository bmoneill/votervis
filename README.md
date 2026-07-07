<div align="center">
    <h1><b>votervis</b></h1>
    <h4>A voting system visualizer</h4>
</div>

## Overview

This program is a voting system visualizer that allows users to simulate elections
using different electoral systems. It provides a CLI interface to input
candidates and ballots, and then displays the results of the election based on
the selected voting system.

## Features

- Supports 8 different voting systems:
  - First Past the Post (Plurality)
  - Two-Round System (Majority runoff)
  - Ranked-Choice Voting (Instant runoff)
  - Single Transferable Vote (Multi-seat proportional)
  - Borda Count (Positional scoring)
  - Approval Voting (candidate with most approvals wins)
  - Condorcet (pairwise comparison)
  - Additional Member System (Combination of proportional and plurality)
- Allows users to input candidates and ballots through a command-line interface.
- Candidate, ballot generation
- Displays election results in a clear and concise manner.

## Installation

To install votervis, follow these steps:

1. Clone the repository

2. Navigate to the project directory

3. Install the required dependencies using pip (optionally using a venv):

   ```bash
   pip install -r requirements.txt
   ```

4. Run the program using the command:

   ```bash
   python main.py
   ```

## To-Do

- Implement a GUI for easier interaction.
- Implement additional voting systems
- Add support for JSON import/export of candidates and ballots

## License

Copyright (c) 2026 Ben O'Neill <ben@oneill.sh>. This work is released under
the terms of the MIT License. See [LICENSE](LICENSE) for the license terms.
