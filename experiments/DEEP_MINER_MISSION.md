# Wave 5: The Deep Miner (24-Hour Persistence)
MISSION: Break the 1000-cycle floor through massive evolutionary search.
CONSTRAINTS: You have 23 hours of VM time. Bit-perfection is mandatory.
MANDATE:
1. DESIGN: Create an evolutionary script ('miner.py') that permutes scheduler windows, seeds, and ALU-offload strategies.
2. DAEMONIZE: Launch using 'nohup python3 miner.py > miner.log 2>&1 &'.
3. JOURNAL: Maintain 'MINER_JOURNAL.md' with the best cycles found every hour.
4. ARCHIVE: Once the daemon is verified running, you may exit. The VM will continue the work.
5. ASSETS: Use all hints in experiments/STRATEGIC_HINTS.md.
