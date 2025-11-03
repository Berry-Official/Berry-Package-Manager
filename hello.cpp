#include <opencv2/opencv.hpp>
#include <opencv2/dnn.hpp>
#include <iostream>
#include <fstream>
#include <vector>
#include <string>

using namespace cv;
using namespace dnn;
using namespace std;

// Load class names from coco.names
vector<string> loadClassNames(const string& file) {
    vector<string> classList;
    ifstream ifs(file.c_str());
    string line;
    while (getline(ifs, line)) {
        classList.push_back(line);
    }
    return classList;
}

int main() {
    // Paths
    string modelPath = "C:/Users/Student/yolov5/yolov5l.onnx";
    string classFile = "C:/Users/Student/yolov5/coco.names"; // put coco.names here
    string videoPath = "C:/Users/Student/Desktop/video (2).mp4";

    // Load class names
    vector<string> classNames = loadClassNames(classFile);
    if (classNames.empty()) {
        cerr << "Error: Failed to load class names.\n";
        return -1;
    }

    // Load the YOLOv5 ONNX model
    Net net = readNetFromONNX(modelPath);
    net.setPreferableBackend(DNN_BACKEND_OPENCV);
    net.setPreferableTarget(DNN_TARGET_CPU);
    // Optional: GPU
    // net.setPreferableBackend(DNN_BACKEND_CUDA);
    // net.setPreferableTarget(DNN_TARGET_CUDA);

    // Load video
    VideoCapture cap(videoPath);
    if (!cap.isOpened()) {
        cerr << "Error: Cannot open video.\n";
        return -1;
    }

    int inputWidth = 640;
    int inputHeight = 640;
    float confThreshold = 0.4;
    float nmsThreshold = 0.45;

    Mat frame;
    while (cap.read(frame)) {
        // Preprocess input
        Mat blob;
        blobFromImage(frame, blob, 1.0 / 255.0, Size(inputWidth, inputHeight), Scalar(), true, false);
        net.setInput(blob);

        // Forward pass
        vector<Mat> outputs;
        net.forward(outputs, net.getUnconnectedOutLayersNames());

        // Post-processing
        vector<int> classIds;
        vector<float> confidences;
        vector<Rect> boxes;

        float* data = (float*)outputs[0].data;
        const int dimensions = outputs[0].size[2];
        const int rows = outputs[0].size[1];

        for (int i = 0; i < rows; ++i) {
            float objectness = data[4];
            if (objectness < confThreshold) {
                data += dimensions;
                continue;
            }

            Mat scores(1, classNames.size(), CV_32FC1, data + 5);
            Point classIdPoint;
            double maxClassScore;
            minMaxLoc(scores, 0, &maxClassScore, 0, &classIdPoint);

            if (maxClassScore > confThreshold) {
                float cx = data[0];
                float cy = data[1];
                float w = data[2];
                float h = data[3];

                int left = int((cx - w / 2) * frame.cols / inputWidth);
                int top = int((cy - h / 2) * frame.rows / inputHeight);
                int width = int(w * frame.cols / inputWidth);
                int height = int(h * frame.rows / inputHeight);

                classIds.push_back(classIdPoint.x);
                confidences.push_back((float)(maxClassScore * objectness));
                boxes.emplace_back(left, top, width, height);
            }
            data += dimensions;
        }

        // Apply NMS
        vector<int> indices;
        NMSBoxes(boxes, confidences, confThreshold, nmsThreshold, indices);

        for (int idx : indices) {
            Rect box = boxes[idx];
            int classId = classIds[idx];

            rectangle(frame, box, Scalar(0, 255, 0), 2);

            string label = format("%s: %.2f", classNames[classId].c_str(), confidences[idx]);
            int baseLine;
            Size labelSize = getTextSize(label, FONT_HERSHEY_SIMPLEX, 0.5, 1, &baseLine);
            int top = max(box.y, labelSize.height);
            rectangle(frame, Point(box.x, top - labelSize.height),
                Point(box.x + labelSize.width, top + baseLine),
                Scalar(0, 255, 0), FILLED);
            putText(frame, label, Point(box.x, top), FONT_HERSHEY_SIMPLEX, 0.5, Scalar(0, 0, 0), 1);
        }

        imshow("YOLOv5m ONNX Detection", frame);
        if (waitKey(1) == 'q') break;
    }

    cap.release();
    destroyAllWindows();
    return 0;
}
