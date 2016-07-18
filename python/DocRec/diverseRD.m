% Diverse RD

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


function [S St H]=diverseRD(dID,D,x,NDResults,title,weight)
j=1;
H=[];
for i=1:size(dID,2)
        S{j}=[];
        Doc{j}=[];
        Titl{j}=[];
        j=j+1;
end
J=j;

for i=1:NDResults
    for z=1:size(dID,2)%Number of lists
        for t=1:size(dID{z},1)%Number of Ids in each list
            if (size(dID{z},2)~=0)
                clear STemp TopicTemp
                for k=1:size(dID,2)
                    STemp{k}=S{k};
                    TopicTemp{k}=Doc{k};
                end
                STemp{z}=[];
                STemp{z}=cat(1,S{z},dID{z}(t));
                TopicTemp{z}=[];
                TopicTemp{z}=cat(1,Doc{z},D{z}(t));
                %calculate the cumulative reward value
                out{z}(t)=DiverseList2(STemp,TopicTemp,x,weight);
            end
        end
    end
   
    [C I]=cellfun(@max,out);
    maxvalue=max(C);

    for z=1:size(I,2)%number of lists
        if out{z}(I(z))==maxvalue
            %dID{z}
            %I(z)
            if(~isempty(dID))
                S{z}=cat(1,S{z},dID{z}(I(z)));
                dID{z}(I(z))=[];
                Doc{z}=cat(1,Doc{z},D{z}(I(z)));
                D{z}(I(z))=[];
                Titl{z}=cat(1,Titl{z},title{z}(I(z))); 
                H=cat(1,H,title{z}(I(z)));
                title{z}(I(z))=[];
                break;
            end
        end
    end
end
St=Titl;
