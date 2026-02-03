.PHONY: all clean clean-all report report-clean

all: 04_phase1_final_report.html

report: 04_phase1_final_report.html

report-clean: 04_phase1_final_report_clean.html

04_phase1_final_report.html: 04_phase1_final_report.ipynb
	quarto render 04_phase1_final_report.ipynb

04_phase1_final_report_clean.html: 04_phase1_final_report_clean.ipynb
	quarto render 04_phase1_final_report_clean.ipynb

clean:
	rm -f 04_phase1_final_report.html
	rm -rf 04_phase1_final_report_files/

clean-all: clean
	rm -f 04_phase1_final_report_clean.html
	rm -rf 04_phase1_final_report_clean_files/
