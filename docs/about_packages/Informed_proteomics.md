## Overall

To help ensure proper download and installation of the Informed Proteomics package, and also give users an initial test-drive using the tool, we have created this tutorial. This will run ProMex feature detection and also MSPathFinder database search on a simplified mzML file and output the result. Please follow these steps:

Download the current Informed-Proteomics_Installer.exe from the releases page: GitHub Releases
Install Informed-Proteomics by running Informed-Proteomics_Installer.exe.
Download the tutorial files: Tutorial_Files.zip
Extract the tutorial files to your preferred location
Zip file contents:

CPTAC_Intact_rep3_15Jan15_Bane_C2-14-08-02RZ_7000-7300.mzML.gz
Scans 7000-7300 of a dataset
MSPathFinder_Mods.txt
Search modifications
HomoSapiens_Uniprot_2015-04-22_tiny.fasta
A small subset of a Homo sapiens fasta file (198 proteins)
To ensure reasonable runtime of the tutorial on a desktop computer, we have limited the MS/MS spectrum file and the protein sequence database. On a system running Windows 7 64-bit, with a Intel Core i7-3770 3.4GHz CPU and 32GB RAM, the MSPathFinderT portion of this tutorial took 43 minutes.

Open Informed-Proteomics command line
Informed Proteomics does not have a graphical interface. The program is operated using a set of commands through the Windows command line. To access this, do the following two steps (see image).

Start Menu->All Programs->Informed-Proteomics->Command Line
This adds information to the command line so that you don't need to know the location of the MSPathFinderT program. 
Change directory to the directory where the tutorial files were extracted. This is done using 'cd' at the command prompt (see image). After changing to the correct directory, you should be able to verify this by listing the directory contents and seeing the files downloaded previously. This is done using 'dir'. 
Run the tools
After navigating to the proper directory, you will have to run the commands shown below to run the three tools: PBFGen, ProMex and MSPathFinderT. Each program is run using the command line by typing in the correct parameters. For this tutorial, you should be able to type in exactly what you see below.

Run PBFGen
PBFGen.exe -s CPTAC_Intact_rep3_15Jan15_Bane_C2-14-08-02RZ_7000-7300.mzML.gz

Run ProMex
ProMex.exe -i CPTAC_Intact_rep3_15Jan15_Bane_C2-14-08-02RZ_7000-7300.pbf -minCharge 2 -maxCharge 60 -minMass 2000 -maxMass 50000 -score n -csv n -maxThreads 0

Run MSPathFinderT
MSPathFinderT.exe -s CPTAC_Intact_rep3_15Jan15_Bane_C2-14-08-02RZ_7000-7300.pbf -feature CPTAC_Intact_rep3_15Jan15_Bane_C2-14-08-02RZ_7000-7300.ms1ft -d HomoSapiens_Uniprot_2015-04-22_tiny.fasta -o .\  -t 10 -f 10 -m 1 -tda 1 -minLength 21 -maxLength 300 -minCharge 2 -maxCharge 30 -minFragCharge 1 -maxFragCharge 20 -minMass 3000 -maxMass 50000 -mod MSPathFinder_Mods.txt

Results
When you finish running, there should be a set of files in the output directory. The ".param" file documents the parameters that were used in the analysis, such as the number and type of post-translational modifications used in the database search. A file with the suffix ".ms1ft" contains information on the LC-MS features including their quantitative abundance. A file with the suffix "_IcTda.tsv" contains the spectrum identification results of a target decoy analysis. The two files are linked through the index of the LC-MS feature. In the .ms1ft file, this is the column labeled FeatureID. In the _IcTda.tsv file, this is the column MS1features.




## PBFGen

PBFGen reads in instrument data files and converts them to PBF files, the format used elsewhere in the Informed-Proteomics suite.

Input format support
Supported natively
*.mzML and *.mzML.gz
Supported with additional software
Note: x86/x64 matter with these additional softwares. PBFGen and other Informed-Proteomics tools that try to read these formats will give you an error if you do not have a correct version installed, telling you which version you need to install.

*.raw (Thermo *.raw format)
Assuming you run this program on a 64-bit computer, reading Thermo Finnigan .raw files is supported via the included RawFileReader DLLs (no additional software install required).
The following formats (and others) can be read if 64-bit ProteoWizard is installed (Download here):
*.mzXML, *.mzXML.gz
*.raw (Thermo *.raw format, also can be read via Thermo MSFileReader)
*.mzML, *.mzML.gz (Supported internally, but used for reading gzipped mzML files when available for speed/memory usage purposes)
*.mgf (Mascot Generic Format)
*.d folders (Agilent and Bruker .d folder formats)
*.wiff (AB Sciex *.wiff format)
*.u2, FID (older Bruker formats)
*.raw folders (Waters *.raw folder format)
*.lcd (Shimadzu *.lcd format)
Input format warning
We have only fully tested PBFGen, ProMex and MSPathFinder on *.mzML, *.mzML.gz, *.raw (Thermo), *.mzXML, and *.mzXML.gz formats (with centroided data in the mzML and mzXML formats; with Thermo *.raw we use Thermo's centroiding for profile data). While the full list of files above can be read for conversion into PBF, their valid conversion into PBF or their utility for performing feature finding or database searches is not tested and cannot be guaranteed in any fashion. For best results, the file provided to PBFGen or other tools in the Informed-Proteomics suite should contain scan data with MS and MS/MS data, with centroided peaks (when not a vendor format).

PBFGen Syntax
PbfGen version 1.0.7569 (September 21, 2020)

Usage: PbfGen.exe

  -?, -help            Show this help screen

  -s, arg#1            Required. Raw file path: *.raw or directory. (also
                       supports other input formats, see documentation)

  -o                   Output directory. Defaults to directory containing input
                       file.

  -start               Start scan number (use to limit scan range included in
                       .pbf file). (Default: -1, Min: -1)

  -end                 End scan number (use to limit scan range included in .pbf
                       file). (Default: -1, Min: -1)

  -ParamFile           Path to a file containing program parameters. Additional
                       arguments on the command line can supplement or override
                       the arguments in the param file. Lines starting with '#'
                       or ';' will be treated as comments; blank lines are
                       ignored. Lines that start with text that does not match a
                       parameter will also be ignored.

  -CreateParamFile     Create an example parameter file. Can supply a path; if
                       path is not supplied, the example parameter file content
                       will output to the console.

  NOTE:                arg#1, arg#2, etc. refer to positional arguments, used
                       like "AppName.exe [arg#1] [arg#2] [other args]".
Examples
These commands will create MyDataset.pbf in the same directory as MyDataset.raw or MyDataset.mzML:

PbfGen.exe -s MyDataset.raw
PbfGen.exe -s MyDataset.mzML
These commands will create MyDataset.pbf in the directory C:\WorkFolder:

PbfGen.exe -s MyDataset.raw -o C:\WorkFolder
PbfGen.exe -s MyDataset.mzML -o C:\WorkFolder
Optionally use -start and -end to limit the scan range to include in the .pbf file

PbfGen.exe -s Dataset.raw -start 2000 -end 3000
System Requirements and Recommendations
Minimum required:

.NET 4.7.2
Minimum recommended:

2.4 GHz, quad-core CPU
16 GB RAM
Windows 7 or newer
250 GB hard drive
PBFGen needs a good amount of RAM available when writing the MS1 and MSn Full XICs, due to a need to hold a larger number of peaks in memory and sort them before writing them to disk. It will try to scale the amount it holds it memory according to the amount of free memory when it starts, but it does have a lower limit that it requires based on the number of scans in the input file. The amount of memory available can drastically affect the time it takes to process and write the full XICs to disk; the more memory available, the less time it may take.

The output file size will often be larger than the input file size, due to the data duplication in the PBF format to reduce the processing time for other programs. The primary exception to this is with data that is stored in profile mode, since the data will be centroided (if possible) before it is written in the PBF format.



The PBF (PNNL Binary Format) file format was created to optimize data access for feature-finding and database searching.

Background
Many mass spectrometry data formats (particularly those used for proteomics) focus on scans - each scan has metadata and peak data. This has worked well in the past, and tools are written to handle the data as such. The main limitation we encountered was the speed at which we could read peak data for an eXtracted Ion Chromatogram, which is heavily used in the feature-finding and database search libraries within Informed-Proteomics. With all of those existing formats, we have to check every scan in the desired range for peaks within the tolerance, requiring extra computational time and lots of little reads from the hard drive to get the desired eXtracted Ion Chromatogram. The PNNL Binary Format was designed to provide the needed scan data, as well as fast access to eXtracted Ion Chromatograms and fast searching for scans by precursor m/z, MSLevel and elution time.

Format basic description
The PBF file format has the following basic structure:

Scan Information
Scan metadata
Scan peaks
m/z and intensity pairs
MS1 Full XIC
All peaks from all MS1 scans, sorted by m/z ascending
Data written: m/z, intensity, and scan number
MSn Full XIC
All peaks from all MSn scans, sorted by m/z ascending
Data written: m/z, intensity, and scan number
File metadata, for fast loading of a PBF file
Minimum and maximum scan numbers
Scan numbers, MSLevels, Elution times, and binary offsets for all scans, with Isolation Window information for MS2 scans
MS1 Full XIC metadata - binary offsets for binned m/z values, used for quickly finding (in the MS1 Full XIC) peaks within a set tolerance of an m/z value
Checksum of the original spectrum file
Some format information about the original spectrum file (for outputting correct information to mzid files)
Binary offsets for the MS1 and MSn full XICs, and for the file metadata section
PBF file format version string


## Promex

ProMex is an LC-MS feature extraction tool that detects isotopomer envelopes of intact protein ions and determines their monoisotopic masses and abundances. The detected features are output to a .ms1ft file containing information including monoisotopic mass, range of charge states, elution-time span (consecutive spectra) and abundance.

Inputs
An instrument file or previously created .pbf file
Command line options
Outputs
A *.ms1ft file
A *_ms1ft.png image of features
A *.pbf file (if a .pbf file was not provided)
ProMex Syntax
ProMex version 1.0.7569 (September 21, 2020)

Usage: ProMex.exe

  -?, -help            Show this help screen

  -i, arg#1            Required. Input file or input folder; supports .pbf,
                       .mzML, and several vendor formats (see documentation)

  -o                   Output directory. (Default: directory containing input
                       file)

  -minCharge           Minimum charge state (Default: 1, Min: 1, Max: 60)

  -maxCharge           Maximum charge state (Default: 60, Min: 1, Max: 60)

  -minMass             Minimum mass in Da (Default: 2000, Min: 600, Max: 100000)

  -maxMass             Maximum mass in Da (Default: 50000, Min: 600,
                       Max: 100000)

  -featureMap          Output the feature heatmap (Default: True)

  -score               Output extended scoring information (Default: False)

  -maxThreads          Max number of threads to use (Default: 0 (automatically
                       determine the number of threads to use))

  -csv                 Also write feature data to a CSV file (Default: False)

  -scoreTh             Likelihood score threshold (Default: -10)

  -ms1ft               ms1ft format feature file path (use '.' to infer the name
                       from the pbf file)

  -ParamFile           Path to a file containing program parameters. Additional
                       arguments on the command line can supplement or override
                       the arguments in the param file. Lines starting with '#'
                       or ';' will be treated as comments; blank lines are
                       ignored. Lines that start with text that does not match a
                       parameter will also be ignored.

  -CreateParamFile     Create an example parameter file. Can supply a path; if
                       path is not supplied, the example parameter file content
                       will output to the console.

  NOTE:                arg#1, arg#2, etc. refer to positional arguments, used
                       like "AppName.exe [arg#1] [arg#2] [other args]".
Examples
With a previously created .pbf file:

ProMex.exe -i MyDataset.pbf -minCharge 2 -maxCharge 60 -minMass 3000 -maxMass 50000 -score n -csv n -maxThreads 0
With a instrument/spectra file:

ProMex.exe -i MyDataset.raw -minCharge 2 -maxCharge 60 -minMass 3000 -maxMass 50000 -score n -csv n -maxThreads 0
ProMex.exe -i MyDataset.mzML -minCharge 2 -maxCharge 60 -minMass 3000 -maxMass 50000 -score n -csv n -maxThreads 0
To create a PNG of the features in an existing ms1ft file (requires both a .pbf file and a .ms1ft file):

ProMex.exe -i dataset.pbf -ms1ft dataset.ms1ft -featureMap
System Requirements and Recommendations
Minimum required:

.NET 4.7.2
Minimum recommended:

2.4 GHz, quad-core CPU
16 GB RAM
Windows 7 or newer
250 GB hard drive


## MSPathfinder

MSPathFinderT finds peptides in top-down LC-MS/MS datasets. Similar to database search engines for bottom-up, it takes a fasta file, a spectrum file, and a list of modifications as an input and reports proteoform spectrum matches (PsSMs) and their scores. These results are output in a tab-separated format and in a MzIdentML file.

Inputs
An instrument file or previously created .pbf file
A previously created .ms1ft file (optional)
Can also read .msalign from MS-Align+, or _isos.csv from ICR2LS or Decon2LS
Command line options
Outputs
A *_IcTarget.tsv file (if target search done)
A *_IcDecoy.tsv file (if decoy search done)
A *_IcTda.tsv file (if target and decoy searches done)
A *.mzid file
A *.ms1ft (if feature file not provided)
A *_ms1ft.png image of features (if feature file not provided)
A *.pbf file (if a .pbf file was not provided)
MSPathFinderT Syntax
MSPathFinderT version 1.0.7569 (September 21, 2020)

Usage: MSPathFinderT.exe

  -?, -help              Show this help screen

  -s, -specFile, arg#1   Required. Spectrum File (*.raw)

  -d, -database          Required. Database File (*.fasta or *.fa or *.faa)

  -o, -outputDir         Output Directory

  -ic                    Search Mode (Default: SingleInternalCleavage (or 1))
                         Possible values are:
                           0 or 'NoInternalCleavage': No Internal Cleavage
                           1 or 'SingleInternalCleavage': Single Internal Cleavage
                           2 or 'MultipleInternalCleavages': Multiple Internal
                           Cleavages

  -tagSearch             Include Tag-based Search (use true or false;
                         or use '0' for false or '1' for true) (Default: True)

  -n,                    Number of results to report for each mass spectrum
  -NumMatchesPerSpec     (Default: 1)

  -IncludeDecoy,         Include decoy results in the _IcTda.tsv file
  -IncludeDecoys         (Default: False)

  -mod                   Path to modification file that defines static and dynamic
                         modifications. Modifications can alternatively be defined
                         in a parameter file, as specified by /ParamFile or
                         -ParamFile
                         Modifications defined using the -mod switch take
                         precedence over modifications defined in a parameter file
                         (Default: empty string, meaning no modifications)

  -tda                   Database search mode:
                         0: don't search decoy database,
                         1: search shuffled decoy database
                         (Default: 0, Min: -1, Max: 1)

  -t, -precursorTol,     Precursor Tolerance (in PPM) (Default: 10)
  -PMTolerance

  -f, -fragmentTol,      Fragment Ion Tolerance (in PPM) (Default: 10)
  -FragTolerance

  -minLength             Minimum Sequence Length (Default: 21, Min: 0)

  -maxLength             Maximum Sequence Length (Default: 500, Min: 0)

  -minCharge             Minimum precursor ion charge (Default: 2, Min: 1)

  -maxCharge             Maximum precursor ion charge (Default: 50, Min: 1)

  -minFragCharge         Minimum fragment ion charge (Default: 1, Min: 1)

  -maxFragCharge         Maximum fragment ion charge (Default: 20, Min: 1)

  -minMass               Minimum sequence mass in Da (Default: 3000)

  -maxMass               Maximum sequence mass in Da (Default: 50000)

  -feature               *.ms1ft, *_isos.csv, or *.msalign (Default: Run ProMex)

  -threads               Maximum number of threads, or 0 to set automatically
                         (Default: 0, Min: 0)

  -act,                  Activation Method (Default: Unknown (or 6))
  -ActivationMethod      Possible values are:
                           0 or 'CID'
                           1 or 'ETD'
                           2 or 'HCD'
                           3 or 'ECD'
                           4 or 'PQD'
                           5 or 'UVPD'
                           6 or 'Unknown'

  -scansFile             Text file with MS2 scans to process

  -flip                  If specified, FLIP scoring code will be used
                         (supports UVPD spectra) (Default: False)

  -ParamFile             Path to a file containing program parameters. Additional
                         arguments on the command line can supplement or override
                         the arguments in the param file. Lines starting with '#'
                         or ';' will be treated as comments; blank lines are
                         ignored. Lines that start with text that does not match a
                         parameter will also be ignored.

  -CreateParamFile       Create an example parameter file. Can supply a path; if
                         path is not supplied, the example parameter file content
                         will output to the console.

  NOTE:                  arg#1, arg#2, etc. refer to positional arguments, used
                         like "AppName.exe [arg#1] [arg#2] [other args]".
Runtime notes
Different command line options can result in drastically different runtimes, particularly the -m SearchMode parameter.

If the SearchMode is 2, the search will be relatively fast (<1 hour usually); for SearchMode 1, it is slower due to the added complexity (1-12 hours usually); for SearchMode 0, it will be significantly slower, especially for larger protein collections and richer datasets (runtime is usually on the order of days, but can reach weeks).
Enabling tag-based searching with -tagSearch 1 can give 5% to 10% more matches, but can increase the runtime by 30% to 50%.
Examples
With previously created .pbf and .ms1ft files:

MSPathFinderT.exe -s MyDataset.pbf -feature MyDataset.ms1ft -d C:\FASTA\ProteinList.fasta -o C:\WorkFolder -t 10 -f 10 -m 1 -tda 1 -minLength 21 -maxLength 300 -minCharge 2 -maxCharge 30 -minFragCharge 1 -maxFragCharge 15 -minMass 3000 -maxMass 50000 -mod MSPathFinder_Mods.txt

With a instrument/spectra file:

MSPathFinderT.exe -s MyDataset.raw -d C:\FASTA\ProteinList.fasta -o C:\WorkFolder -t 10 -f 10 -m 1 -tda 1 -minLength 21 -maxLength 300 -minCharge 2 -maxCharge 30 -minFragCharge 1 -maxFragCharge 15 -minMass 3000 -maxMass 50000 -mod MSPathFinder_Mods.txt

MSPathFinderT.exe -s MyDataset.raw -d C:\FASTA\ProteinList.fasta -o C:\WorkFolder -t 10 -f 10 -m 1 -tda 1 -minLength 21 -maxLength 300 -minCharge 2 -maxCharge 30 -minFragCharge 1 -maxFragCharge 15 -minMass 3000 -maxMass 50000 -mod MSPathFinder_Mods.txt

Using a parameter file:

MSPathFinderT.exe -s C:\WorkDir\Dataset.pbf -feature C:\WorkDir\Dataset.ms1ft -d C:\WorkDir\Proteins.fasta -o C:\WorkDir  /ParamFile:C:\WorkDir\MSPF_MetOx_CysDehydro_NTermAcet_SingleInternalCleavage_ReportTop2.txt

System Requirements and Recommendations
Minimum required:

.NET 4.7.2
Minimum recommended:

2.4 GHz, quad-core CPU
16 GB RAM
Windows 7 or newer
250 GB hard drive
