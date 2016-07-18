% Diverse List 2

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



function [out]=DiverseList2(S,TopicS,x,weight)
S;
TopicS;
size(S,2);
out=0;
%calculate the cumulative reward value
for j=1:size(S,2)
	PerList(j)=0;
    for i=1:size(S{j},1)% Sj is index of document from listj
        %the contribution of ith doc in list j is given by TopicS{j}{i}
        %which is multiplied by the weight of the implicit query and added
        %to the contribution of the list
        PerList(j)=PerList(j)+TopicS{j}(i)*(weight(j)/(sum(weight)));% compute sigma (SQR())
    end
    % reward of list j , x is \lambda in the manuscript
	out=out+(PerList(j)).^x;
end
