# Báo cáo Day 09 — Trần Thị Ngọc Ánh (2A202603157)

## 1. Kết luận trước

Pipeline kết luận **Hold**. Lô đầu vào có 224 ảnh, giữ lại 193/224 ảnh và loại 31/224 ảnh. Sau duyệt mô phỏng 80/80 ảnh theo ngân sách, còn 0 lỗi bắt buộc và 34/193 ảnh có cảnh báo chưa duyệt (17,62%), vượt ngưỡng Hold 10%. Bộ dữ liệu `submission/export/clean_v1` được xuất dưới dạng bản nháp để thử nghiệm.

## 2. Lỗi và phân việc

| Mã lỗi | Số ảnh/dòng | Ai sửa | Vì sao |
|---|---|---|---|
| `BAD_CLASS_ID` | 6 ảnh / 6 dòng | Máy | Xóa dòng có ID lớp sai. |
| `BAD_CLASS_NAME` | 2 dòng cấp dataset | Máy | Đồng bộ tên lớp theo cấu hình. |
| `BAD_FORMAT` | 3 ảnh / 3 dòng | Máy | Xóa dòng sai định dạng. |
| `BAD_SIZE` | 3 ảnh / 3 dòng | Máy | Loại ảnh sai kích thước. |
| `BOX_HUGE` | 3 ảnh / 3 dòng | Người | Đối chiếu ảnh để xác nhận cảnh báo. |
| `BOX_OUT_OF_IMAGE` | 8 ảnh / 8 dòng | Máy | Cắt box về biên hoặc xóa nếu nằm hẳn ngoài ảnh. |
| `BOX_TINY` | 4 ảnh / 6 dòng | Người | Đối chiếu ảnh để xác nhận cảnh báo. |
| `BOX_ZERO` | 4 ảnh / 4 dòng | Máy | Xóa box không có diện tích. |
| `CLASS_RARE` | 4 dòng cấp dataset | Người | Đánh giá độ phủ của lớp trong lô dữ liệu. |
| `CORRUPT_IMAGE` | 2 ảnh / 2 dòng | Máy | Loại ảnh hỏng. |
| `DUP_BOX` | 7 ảnh / 7 dòng | Máy | Xóa dòng box lặp. |
| `DUP_IMAGE_EXACT` | 8 ảnh / 8 dòng | Máy | Loại ảnh được xác định là trùng. |
| `DUP_IMAGE_NEAR` | 7 ảnh / 7 dòng | Máy | Loại ảnh được xác định là trùng. |
| `EMPTY_LABEL` | 11 ảnh / 11 dòng | Người | Đối chiếu ảnh để xác nhận cảnh báo. |
| `LEAK_TEST` | 11 ảnh / 11 dòng | Máy | Loại ảnh rò rỉ từ tập test. |
| `MISSING_LABEL_FILE` | 6 ảnh / 6 dòng | Người | Xem ảnh và tạo nhãn. |
| `POSSIBLE_FALSE_POS` | 23 ảnh / 24 dòng | Người | Đối chiếu ảnh để xác nhận cảnh báo. |
| `POSSIBLE_LOOSE_BOX` | 23 ảnh / 27 dòng | Người | Đối chiếu ảnh để xác nhận cảnh báo. |
| `POSSIBLE_MISSING` | 52 ảnh / 53 dòng | Người | Đối chiếu ảnh để xác nhận cảnh báo. |
| `POSSIBLE_WRONG_CLASS` | 17 ảnh / 17 dòng | Người | Đối chiếu ảnh để xác nhận cảnh báo. |

Ảnh `img_0020` đứng đầu hàng đợi với điểm **11.524** và các cờ `FIXED_DROP_LINE`, `POSSIBLE_MISSING`, `POSSIBLE_WRONG_CLASS`. Trong 80 ảnh đã duyệt, có 74 ảnh mang cảnh báo ngữ nghĩa ở vòng QC 2. Các ảnh được duyệt chứa 94/120 cảnh báo ngữ nghĩa của vòng này. Đây là số cảnh báo được đưa ra xem xét, còn việc xác nhận lỗi thật cần đối chiếu ảnh.

## 3. Calibration (2 ngưỡng)

| Tham số | Khởi đầu | Đã chọn | Precision / Recall trước → sau | Lý do |
|---|---:|---:|---|---|
| `duplicates.phash_dist` | 2 | 16 | Ảnh gần trùng: P 1,00 → 1,00, R 0,50 → 0,83 | Phát hiện thêm ảnh gần trùng, từ 3/6 lên 5/6 ca calib. |
| `second_opinion.conf` | 0.25 | 0.6 | Thiếu nhãn: P 0,50 → 0,57, R 1,00 → 1,00. Sai lớp: P 0,56 → 0,62, R 0,83 → 0,83. | Giữ recall thiếu nhãn, tăng precision sai lớp. Recall box lỏng giảm từ 0,40 xuống 0,20. |

Precision 1,00 của ảnh gần trùng chỉ được đo trên tập calib có 6 ca ảnh gần trùng. Trong lô chính, vòng QC 1 ghi 7 dòng `DUP_IMAGE_NEAR`. Cần mở các cặp tương ứng để xác nhận vì ảnh khác nhau có thể có pHash gần nhau.

## 4. Cửa chặn và điều pipeline KHÔNG bắt được

**(a) Kiểm tra gate.** Chạy riêng với `--budget 0`, ghi báo cáo tại `work/rep_nb` và chỉ định thư mục xuất `work/exp_nb`. Khi không có người duyệt để xử lý ảnh thiếu file nhãn, gate trả **Rework**, mã thoát **20**, và không tạo manifest xuất dataset.

**(b) Điểm mù.** Trên tập calib, ở `conf = 0.6`, bộ kiểm chỉ phát hiện **1/5** ca box lỏng. Ở `phash_dist = 16`, bộ kiểm phát hiện **5/6** ca ảnh gần trùng, còn **1/6** ca bị bỏ sót.

## 5. Train: raw vs clean (tùy chọn, chấm riêng)

Train YOLO26n trong 20 epoch với seed 0 và 1, rồi đánh giá trên cùng 100 ảnh test. mAP50 trung bình tăng từ 0,72575 (raw) lên 0,72940 (clean), tức +0,365 điểm phần trăm. mAP50–95 giảm từ 0,51170 xuống 0,49960. Độ lệch chuẩn mẫu của mAP50 giữa hai seed là 0,00021 với raw và 0,00240 với clean. Với hai seed, chưa đủ cơ sở kết luận clean cải thiện ổn định. Bản clean dùng để train là bản nháp ở trạng thái Hold.

Hai giả thuyết cần kiểm tra là ảnh bị gắn cờ LEAK_TEST có thể làm điểm raw lạc quan hơn, và bản clean vẫn còn 34/193 ảnh có cảnh báo chưa duyệt. Có thể kiểm tra bằng cách chạy lại raw sau khi loại riêng các ảnh LEAK_TEST, rồi thử một bản clean đã duyệt thêm với cùng cấu hình train.

## 6. Quyết định và ghi chú AI

**Quyết định cuối: Hold.** Cần duyệt tiếp các ảnh còn cảnh báo, sửa các lỗi được xác nhận rồi chạy lại QC. Nếu lô vẫn có 193 ảnh, Release yêu cầu còn **0 lỗi bắt buộc** và **tối đa 19 ảnh** có cảnh báo chưa duyệt để tỉ lệ dưới 10%.

- **Prompt chính:** Nhờ ChatGPT triển khai bốn module QC theo đặc tả và unit test của repo để chạy trên Colab.
- **Cách kiểm:** Chạy pytest, chạy pipeline chính và kiểm tra gate bằng phép thử `--budget 0`.
- **Một điểm đã sửa khi dùng AI:** Hướng dẫn ban đầu dùng ngưỡng `8` làm mốc so sánh pHash. Khi ghi kết quả trước và sau, tôi dùng giá trị khởi đầu `2` đã xác nhận từ YAML.

**Thưởng CVAT.** Bộ lọc `width < 20` khớp **9 box trên 4 ảnh** gồm `img_0020` (3), `img_0030` (3), `img_0124` (1), `img_0135` (2). Số cảnh báo `BOX_TINY` tương ứng ở vòng QC 1 là `img_0020` (0), `img_0030` (0), `img_0124` (0), `img_0135` (0). CVAT lọc theo chiều rộng dưới 20 px, còn pipeline kiểm cạnh ngắn dưới 12 px. Trên `img_0053`, tôi thấy một box nghi gán nhầm vào người trong ảnh in. Người gán có thể dùng `can_review` để đánh dấu box cần kiểm tra lại. Trong pipeline, các cảnh báo được đưa vào `05_review_queue.csv` để người duyệt xem.
