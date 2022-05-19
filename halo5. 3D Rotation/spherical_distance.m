clear; close all; clc;

pts_num = 10000;
rep_num = 2;

dm = -inf(pts_num, rep_num);

for k = 1:rep_num
    xyz = randn(pts_num, 3);
    xyz = bsxfun(@times, xyz, 1./sqrt(sum(xyz.^2, 2)));
    
    for i = 1:pts_num
        d2 = xyz * xyz(i, :)';
        d2(i) = -1;
        dm(i, k) = acos(max(d2));
    end
end

%%
q_max = sqrt(4 / pts_num) * 3;
q_edges = 0:q_max/100:q_max;
q_center = (q_edges(1:end-1) + q_edges(2:end)) / 2;
q_cnts = histcounts(dm(:), q_edges, 'normalization', 'pdf');
q_pdf = (pts_num - 1)/2 * sin(q_center) .* ((1 + cos(q_center)) / 2).^(pts_num - 2);

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
title(sprintf('Uniformly distributed %d points on S(2)', pts_num), 'fontsize', 18);

% saveas(gcf, 'img/hist01.png');