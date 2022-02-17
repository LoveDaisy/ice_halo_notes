clear; close all; clc;

% [xyz, ll, dr] = geo.generate_healpix_grids(6);
% num = size(xyz, 1);

num = 20000;
xyz = randn(num, 3);
xyz = geo.normalize_vector(xyz);

ll = geo.xyz2ll(xyz);
q = geo.llr2quat([ll, rand(num, 1)*360]);

wxyz = randn(num, 4);
wxyz = geo.normalize_vector(wxyz);

figure(1); clf;
utl.plot_data_3d(xyz, [], '.');
axis equal;

xyz_neighbor_dist = inf(num, 1);
q_neighbor_dist = inf(num, 1);
wxyz_neighbor_dist = inf(num, 1);
batch_size = 200;
for i = 1:batch_size:num
    i1 = i;
    i2 = min(i + batch_size, num);
    tmp_mat = pdist2(xyz(i1:i2, :), xyz, 'cosine');
    for j = i1:i2
        tmp_mat(j-i1+1, j) = inf;
    end
    xyz_neighbor_dist(i1:i2) = min(tmp_mat, [], 2);
end
for i = 1:batch_size:num
    i1 = i;
    i2 = min(i + batch_size, num);
    tmp_mat = pdist2(q(i1:i2, :), q, 'cosine');
    for j = i1:i2
        tmp_mat(j-i1+1, j) = inf;
    end
    q_neighbor_dist(i1:i2) = min(tmp_mat, [], 2);
end
for i = 1:batch_size:num
    i1 = i;
    i2 = min(i + batch_size, num);
    tmp_mat = pdist2(wxyz(i1:i2, :), wxyz, 'cosine');
    for j = i1:i2
        tmp_mat(j-i1+1, j) = inf;
    end
    wxyz_neighbor_dist(i1:i2) = min(tmp_mat, [], 2);
end
xyz_neighbor_dist = acos(1 - xyz_neighbor_dist);
q_neighbor_dist = acos(1 - q_neighbor_dist);
wxyz_neighbor_dist = acos(1 - wxyz_neighbor_dist);

%%
figure(2); clf;
[xyz_pdf, xyz_bin_edge] = histcounts(xyz_neighbor_dist, 200, 'Normalization', 'pdf');
xyz_bin_center = (xyz_bin_edge(1:end-1) + xyz_bin_edge(2:end))/2;
k = sin(xyz_bin_center/2).^2 .* (num - 1);
plot(xyz_bin_center, xyz_pdf, ...
    xyz_bin_center, num / 2 * sin(xyz_bin_center) .* (1 - sin(xyz_bin_center/2).^2).^(num - 1), ...
    xyz_bin_center, num / 2 * sin(xyz_bin_center) .* exp(-k));
set(gca, 'xlim', [0, .06]);

figure(3); clf;
[q_pdf, q_bin_edge] = histcounts(q_neighbor_dist, 200, 'Normalization', 'pdf');
q_bin_center = (q_bin_edge(1:end-1) + q_bin_edge(2:end))/2;
plot(q_bin_center, q_pdf, ...
    q_bin_center, 2*num*2/pi*sin(q_bin_center).^2.*((pi - q_bin_center + cos(q_bin_center).*sin(q_bin_center))/pi).^(num*2-1));
set(gca, 'xlim', [0, .2]);

figure(4); clf;
[wxyz_pdf, wxyz_bin_edge] = histcounts(wxyz_neighbor_dist, 200, 'Normalization', 'pdf');
wxyz_bin_center = (wxyz_bin_edge(1:end-1) + wxyz_bin_edge(2:end))/2;
plot(wxyz_bin_center, wxyz_pdf, ...
    wxyz_bin_center, 2*num/pi*sin(wxyz_bin_center).^2.*((pi - wxyz_bin_center + cos(wxyz_bin_center).*sin(wxyz_bin_center))/pi).^(num-1));
set(gca, 'xlim', [0, .2]);

% figure(5); clf;
% utl.plot_data_3d(q, [2,3,4], '.');
% axis equal;