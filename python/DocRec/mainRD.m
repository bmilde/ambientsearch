% Main file.

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


function[documentDC]=mainRD(path)
Files=dir([path '/AllResults/scores*']);
counter=1;
%read lucebe scorese
for countfile=1:length(Files)
    fid1=fopen([path '/AllResults/' Files(countfile).name ],'r');
        tempp=textscan(fid1,'%f');
        isempty(tempp{:});
        if(~isempty(tempp{:}))
            TempDocTopic{counter}=cell2mat(tempp)/norm(cell2mat(tempp));
            counter=counter+1;
        end    
    fclose(fid1);
end
%read the title of retrieved wikipedia articles
Filest=dir([path '/AllResults/Title*']);
counter=1;
for countfile=1:length(Filest)
    fid1=fopen([path '/AllResults/' Filest(countfile).name ],'r');
   t=fgetl(fid1);
    if(~all(t == -1))
        ss=1;
        clear temp
        while ischar(t)
            temp(ss) = cellstr(t);
               ss=ss+1;
            t=fgetl(fid1);   
        end
        dTitle{1,counter}=temp';
        counter=counter+1;
    end
    fclose(fid1);
end
% read the weight of each implicit query
fid1=fopen([path '/Value/v1'],'r');
we=textscan(fid1,'%f');
fclose(fid1);
weight1=we{:};
% read the WPID value of each article
Filesi=dir([path '/AllResults/WPID*']);
counter=1;
for countfile=1:length(Files)
    
    fid1=fopen([path '/AllResults/' Filesi(countfile).name ],'r');
    tempid=textscan(fid1,'%f');
        if(~isempty(tempid{:}))
            dID(counter)=tempid;
           weights(counter)=weight1(countfile);
        counter=counter+1;
        end
    fclose(fid1);
end
te=0;
for i=1:size(dID,2)
te=te+size(dID{i},1);
end
%calling diverse merging method
   [Dxdc DTitledc Hdc]=diverseRD(dID,TempDocTopic,0.75,min(te,15),dTitle,weights);
   size(Hdc);
   % writing documents
   for k=1:size(Hdc)
     documentDC(k,1)=Hdc(k);
   end