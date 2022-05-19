clear; close all; clc;

pts_num = 10000;
rep_num = 2;

dm = -inf(pts_num*2, rep_num);

for k = 1:rep_num
    xyz = randn(pts_num, 3);
    xyz = bsxfun(@times, xyz, 1./sqrt(sum(xyz.^2, 2)));
    llr = [atan2(xyz(:, 2), xyz(:, 1)), asin(xyz(:, 3)), rand(pts_num, 1) * 2 * pi];
    
    q1 = [cos(llr(:, 3) / 2), -sin(llr(:, 3) / 2) * [0, 0, 1]];
    q2 = [cos(pi/4 - llr(:, 2) / 2), -sin(pi/4 - llr(:, 2) / 2) * [0, 1, 0]];
    q3 = [cos(llr(:, 1) / 2), -sin(llr(:, 1) / 2) * [0, 0, 1]];
    qm = quatmultiply(q1, q2);
    q = quatmultiply(qm, q3);
    q = [q; -q];
    
    for i = 1:pts_num*2
        d2 = q * q(i, :)';
        d2(i) = -1;
        dm(i, k) = acos(max(d2));
    end
end

%%
q_max = (4 / pts_num)^0.33 * 2;
q_edges = 0:q_max/100:q_max;
q_center = (q_edges(1:end-1) + q_edges(2:end)) / 2;
q_cnts = histcounts(dm(:), q_edges, 'normalization', 'pdf');

q_pdf = 2*(2*pts_num-1)/pi*(1 - q_center/pi + cos(q_center).*sin(q_center)/pi).^(2*pts_num-2).*sin(q_center).^2;

figure(1); clf;
set(gcf, 'position', [450, 300, [600, 450] * 1.2]);

hold on;
bar(q_center, q_cnts, 'barwidth', 1.0, 'facealpha', 0.5, 'edgecolor', 'none');
plot(q_center, q_pdf, 'linewidth', 2.5);
box on;

set(gca, 'fontsize', 13);
legend({'Empirical histogram', 'Analytical pdf'}, 'fontsize', 13);
xlabel('Nearest neighbor (rad)', 'fontsize', 16);
ylabel('Probability density', 'fontsize', 16);
title(sprintf('Uniformly distributed %d*2 points on S(3)', pts_num), 'fontsize', 18);

% saveas(gcf, 'img/hist02.png');