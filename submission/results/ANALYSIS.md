# Phân tích kết quả train Day 09

- **Kết quả:** YOLO26n chạy 20 epoch với seed 0 và 1, đánh giá trên cùng 100 ảnh test. mAP50 trung bình tăng từ 0,72575 (raw) lên 0,72940 (clean), tương đương +0,365 điểm phần trăm. Độ lệch chuẩn mẫu giữa hai seed là 0,00021 với raw và 0,00240 với clean. mAP50–95 giảm từ 0,51170 xuống 0,49960. Với hai seed, chưa đủ cơ sở kết luận clean cải thiện ổn định.
- **Dữ liệu train:** JSON ghi raw có 224 ảnh đầu vào và clean có 193 ảnh. Khi quét raw, Ultralytics ghi nhận 11 mục corrupt.
- **Kết quả theo lớp:** AP50 trung bình của bus tăng nhiều nhất, từ 0,69490 lên 0,71530. AP50 của truck giảm từ 0,64845 xuống 0,62145. Cần đối chiếu các cảnh báo QC và dự đoán trên tập test để tìm nguyên nhân.
- **Rò rỉ và chất lượng nhãn:** Các ảnh bị gắn cờ LEAK_TEST có thể làm điểm raw cao hơn. Có thể kiểm tra bằng cách train lại raw sau khi loại riêng các ảnh này. Bản clean vẫn ở trạng thái Hold với 34/193 ảnh còn cảnh báo chưa duyệt. Có thể duyệt thêm các ảnh đó rồi train lại với cùng cấu hình để kiểm tra ảnh hưởng của chất lượng nhãn.
