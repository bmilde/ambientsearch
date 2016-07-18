% File with names of text input files.

% Copyright (c) 2015 Idiap Research Institute, http://www.idiap.ch/
% Written by Maryam Habibi <Maryam.Habibi@idiap.ch> or <M1habiby@gmail.com>

% This file is part of the DocRec software.

% DocRec is free software: you can redistribute it and/or modify
% it under the terms of the GNU General Public License version 3 as
% published by the Free Software Foundation.

% DocRec is distributed in the hope that it will be useful,
% but WITHOUT ANY WARRANTY; without even the implied warranty of
% MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
% GNU General Public License for more details.

% You should have received a copy of the GNU General Public License
% along with DocRec. If not, see <http://www.gnu.org/licenses/>.


%path= folder name to write or read the files from there, e.g. path='/idiap/home/mhabibi/public/Results';
path='/var/www/ambientsearch/python/DocRec/';

%Filein = input filename in path/transcripts folder e.g. Filein='temp1';
Filein='<filename_placeholder>';

function [] = TestMaryamTexts(path,Filein)
% delete the folders contain words, retrieval results 
delete([path '/words/*']);
 delete([path '/AllResults/*']);
 % cleaning the input file, loading topic models and representing words by
 % topical information
[X wP wordsw]= readWord1(path,Filein);
%opening folders to write words, all retrieval results, and the final short
%list of results
 mkdir([path '/words'])
 mkdir([path '/AllResults'])
 mkdir([path '/RSL75'])
 % default number of words extracted from each covnersation
kk = <number_placeholder>;

x = X(1,:); 
xP = x*wP;
PQ=sum(xP,1)/sum(x);
%The number of keyword extracted is the minimum between the length of
%conversation and the default number
k = min(kk,sum(x>0));
% p is the diversity factor in the manuscript is represented by \lambda     
p=0.75;
% call keyword extraction module the output is weight and the number of
% keyword in the dictionary
[outw outv]=BeamSearchKeywordExtraction(x, wP, xP,k, p , size(wordsw,1),path);
% extract keywords assigned to each dictionary number
for cou=1:size(outw,2)
    Wo(cou)=wordsw(outw(cou));
end
%Write words in a file 
dlmcell([path '/W/2'],Wo');
%prepare implicit queries
clear r yout in1;
r=(repmat(outv',1,100).*wP).*repmat(PQ,size(wordsw,1),1);
count=1;
for to=1:100
       if(sum(r(:,to))>0)
           inde=find(r(:,to));
           countts=1;
           clear yout in1;
           yo=[];
           for ts=1:sum(r(:,to)>0)
               if(r(inde(ts),to)>=0.01)
                   in1{countts}=inde(ts);
                    yout{countts}=wordsw{inde(ts)};
                    yo=[yo ',' wordsw{inde(ts)}];
                    countts=countts+1;
               end
           end
           if(exist('yout')>0)
                su=0;
                for jj=1:length(in1)
                    su=su+sum(r(in1{jj},:));
                end
                ssu{count}=su;
                % write the words of each implicit query in a separate file
                dlmcell([path '/words/' int2str(count)],yout');
               %run lucene to retrieve documents based on implicit queries
               %yo is yout which is written in the following format
               %"w1,w2,w3,", I mean there is comma between words of an
               %implicit query
              system(['java -jar /path/to/search.jar ' path ' ' [yo ','] ' ' int2str(count)]);
               
               count=count+1;
           end
       end
end
   dlmcell([path '/Value/v1'],ssu');
   %call diverse merging method
   out_doc=mainRD(path);
   out1={};
    k=1;
    [ee,indexDoc] = unique(out_doc,'first');      
    out2=out_doc(sort(indexDoc));
    out=out2(1:min(5,size(out2,1)));
    %write the results in the final list of results
    dlmcell([path '/RSL75/r1'],out);
    Files1=dir([path '/words/*']);
    %Write the number of files with non-empty results
    for i=1:length(Files1)
        gk{i}=Files1(i).name;
    end
    dlmcell([path '/numFiles/1'],gk(3:end)')   
end

