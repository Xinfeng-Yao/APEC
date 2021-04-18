#!/usr/bin/python
import warnings
warnings.filterwarnings("ignore")
#
import os,numpy,pandas,subprocess
from optparse import OptionParser
#
#
opts = OptionParser()
usage = "Merge counts of cells to track files\nusage: %prog -s project --cfile cluster.csv --gsize chrom.sizes"
opts = OptionParser(usage=usage, version="%prog 1.0")
opts.add_option("-s", help="The project folder.")
opts.add_option("--cfile", help="cluster.csv file, e.g. louvain_cluster_by_APEC.csv in <result> folder")
opts.add_option("--gsize", default='../reference/hg19.chrom.sizes', help="chrom.size files, default=../reference/hg19.chrom.sizes")
options, arguments = opts.parse_args()
#
#
def merge_bam(options):
    bam_folder = [x for x in os.listdir(options.s+'/work')]
    bam_folder.sort()
    cell_df = pandas.read_csv(options.cfile, sep='\t', index_col=0)
    if 'notes' in cell_df.columns.values: cell_df['cluster'] = cell_df['notes']
    cell_types = cell_df['cluster'].values
    cell_types = list(set(cell_types))
    for cell_type in cell_types:
        marked_bam, select = [], []
        for folder in bam_folder:
            path = options.s + '/work/' + folder + '/'
            if folder in cell_df.index.values:
                if cell_df.ix[folder, 'cluster']==cell_type:
                    select.append(folder)
                    marked_bam.extend([path + x for x in os.listdir(path) if x[-10:]=='marked.bam'])
        marked_bam = ' '.join(marked_bam)
        merged_bam = options.s + '/result/track/' + str(cell_type) + '.bam'
        subprocess.check_call('samtools merge -f ' + merged_bam + ' ' + marked_bam, shell=True)
        subprocess.check_call('samtools index ' + merged_bam, shell=True)
    return
#
#
def bam2bw(options):
    cell_df = pandas.read_csv(options.cfile, sep='\t', index_col=0)
    if 'notes' in cell_df.columns.values: cell_df['cluster'] = cell_df['notes']
    cell_types = cell_df['cluster'].values
    cell_types = list(set(cell_types))
    for cell_type in cell_types:
        name = options.s+'/result/track/'+str(cell_type)
        cells = cell_df.loc[cell_df['cluster']==cell_type]
        cells = cells.index.values
        subprocess.check_call('bedtools genomecov -bg -ibam '+name+'.bam -g '+options.gsize+' > '+name+'.bedgraph', shell=True)
        subprocess.check_call('bedtools sort -i '+name+'.bedgraph > '+name+'.sorted.bedgraph', shell=True)
        counts = numpy.array([int(x.split()[3]) for x in open(name+'.sorted.bedgraph').readlines()])
        total = counts.sum()
        with open(name+'.sorted.bedgraph') as infile, open(name+'.norm.bedgraph', 'w') as outfile:
            for line in infile:
                words = line.split()
                words[3] = str(round(float(words[3]) * 100.0 / len(cells)))
                outfile.write('\t'.join(words)+'\n')
        subprocess.check_call('bedGraphToBigWig '+name+'.norm.bedgraph '+options.gsize+' '+name+'.bw', shell=True)
    return
#
#
#
if not os.path.exists(options.s+'/result'): subprocess.check_call('mkdir '+options.s+'/result', shell=True)
if not os.path.exists(options.s+'/result/track'): subprocess.check_call('mkdir '+options.s+'/result/track', shell=True)
merge_bam(options)
bam2bw(options)
#
#
#
