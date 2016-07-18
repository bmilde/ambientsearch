% Read Word.

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


function [X wP word] = readWord1(path,FName) 
%stopword list
stopwords_cellstring={'hmmm','wait','si','erm','a'};
    %load topic models 
   topic_word_prob = load('word_topic_prob_dist.mat');
    % load dictionary library with the number of their occurence in the topic space
    directory = load('dict.mat');
    %contains the list of words 
    Sw=size(directory.wordsw,1);
    %initialize an input file with dictionary size
    input=sparse(1,Sw);
for countfile=1:1
    %read input file
     fid11=fopen([path FName ],'r'); 
%remove stopwords and cleaning
   if fid11 > 0
     numbers = textscan(fid11,'%s','whitespace','{,.}[]() ');
     fclose(fid11);
     number = numbers{:};
     temp2=lower(number);
     split1 = regexp(temp2,'\s','Split');
     split2=[split1{:}];
     Sp = strjoin(split2(~ismember(split2,stopwords_cellstring)),' ');
     SpH=regexp(Sp,'\s','Split');
     [rx,ry]=size(SpH);
     H=reshape(SpH,ry,rx);
  end
%represent words with topic information
  IndexH1=[];
  word=directory.wordsw;
  [xh yh]=size(H);
    for i=1:xh
      Ch=strcmp(word,H(i));
        [a b]=max(Ch);
       if (sum(Ch)==0 | ~isempty(find(IndexH1==b)))
           IndexH1(i)=-1;
       else
        [M,IndexH1(i)]=max(Ch);
        Freq(i)=sum(strcmp(H,H(i)));
       end

    end
    s=0;
    for i=1:xh
        if IndexH1(i)==-1;
        else
            s=s+1;
            D(s)=word(IndexH1(i));
            F(s)=Freq(i);
            input(countfile,IndexH1(i))=Freq(i);
        end
    end
  
end
X = input;
wP = topic_word_prob.twp;
end
